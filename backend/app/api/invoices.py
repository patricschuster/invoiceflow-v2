from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import logging

from app.database import get_db
from app.models.invoice import Invoice
from app.models.audit_log import AuditLog
from app.schemas.invoice import (
    Invoice as InvoiceSchema,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceApprove,
    InvoiceReject,
    InvoiceStats,
    InvoiceProcess,
)
from app.services.file_service import FileService
from app.services.invoice_parser import InvoiceParser
from app.services.export_manager import ExportManager
from app.config import settings
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/stats", response_model=InvoiceStats)
async def get_invoice_stats(db: Session = Depends(get_db)):
    """Get invoice statistics"""

    total = db.query(func.count(Invoice.id)).scalar() or 0
    pending = db.query(func.count(Invoice.id)).filter(Invoice.status == "pending").scalar() or 0
    approved = db.query(func.count(Invoice.id)).filter(Invoice.status == "approved").scalar() or 0
    rejected = db.query(func.count(Invoice.id)).filter(Invoice.status == "rejected").scalar() or 0

    # Calculate total amounts
    total_amount_pending = db.query(func.sum(Invoice.amount_gross)).filter(
        Invoice.status == "pending"
    ).scalar() or Decimal("0.00")

    total_amount_approved = db.query(func.sum(Invoice.amount_gross)).filter(
        Invoice.status == "approved"
    ).scalar() or Decimal("0.00")

    return InvoiceStats(
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected,
        total_amount_pending=total_amount_pending,
        total_amount_approved=total_amount_approved,
    )


@router.get("/", response_model=List[InvoiceSchema])
async def get_invoices(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get all invoices with optional status filter"""

    query = db.query(Invoice)

    if status:
        query = query.filter(Invoice.status == status)

    invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceSchema)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get a specific invoice by ID"""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice


@router.post("/", response_model=InvoiceSchema)
async def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new invoice"""

    db_invoice = Invoice(**invoice.model_dump())
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    # Create audit log
    audit_log = AuditLog(
        action="create",
        entity_type="invoice",
        entity_id=db_invoice.id,
        new_values=invoice.model_dump(),
        description=f"Invoice created: {invoice.filename}",
    )
    db.add(audit_log)
    db.commit()

    return db_invoice


@router.patch("/{invoice_id}", response_model=InvoiceSchema)
async def update_invoice(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    db: Session = Depends(get_db),
):
    """Update an invoice"""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Store old values for audit log
    old_values = {
        "invoice_number": invoice.invoice_number,
        "amount_gross": str(invoice.amount_gross) if invoice.amount_gross else None,
        "cost_center": invoice.cost_center,
        "project": invoice.project,
        "tags": invoice.tags,
    }

    # Update fields
    update_data = invoice_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)

    # Create audit log
    audit_log = AuditLog(
        action="update",
        entity_type="invoice",
        entity_id=invoice.id,
        old_values=old_values,
        new_values=update_data,
        description=f"Invoice updated: {invoice.filename}",
    )
    db.add(audit_log)
    db.commit()

    return invoice


@router.post("/{invoice_id}/approve")
async def approve_invoice(
    invoice_id: int,
    approval: InvoiceApprove,
    db: Session = Depends(get_db),
):
    """Approve an invoice and trigger export to accounting and DMS"""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "approved":
        raise HTTPException(status_code=400, detail="Invoice is already approved")

    # Update invoice
    invoice.status = "approved"
    invoice.approved_by = approval.approved_by
    invoice.approved_at = datetime.now(timezone.utc)

    if approval.cost_center:
        invoice.cost_center = approval.cost_center
    if approval.project:
        invoice.project = approval.project
    if approval.tags:
        invoice.tags = approval.tags
    if approval.comment:
        invoice.comment = approval.comment

    db.commit()
    db.refresh(invoice)

    # Create audit log
    audit_log = AuditLog(
        action="approve",
        entity_type="invoice",
        entity_id=invoice.id,
        user=approval.approved_by,
        new_values={
            "status": "approved",
            "approved_by": approval.approved_by,
            "cost_center": approval.cost_center,
            "project": approval.project,
            "tags": approval.tags,
        },
        description=f"Invoice approved by {approval.approved_by}",
    )
    db.add(audit_log)
    db.commit()

    # Export to accounting (Lexware) and DMS (Paperless)
    export_manager = ExportManager(db)
    export_results = export_manager.export_invoice(invoice)
    db.refresh(invoice)

    return {"invoice": InvoiceSchema.model_validate(invoice), "export": export_results}


@router.post("/{invoice_id}/reject", response_model=InvoiceSchema)
async def reject_invoice(
    invoice_id: int,
    rejection: InvoiceReject,
    db: Session = Depends(get_db),
):
    """Reject an invoice"""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "rejected":
        raise HTTPException(status_code=400, detail="Invoice is already rejected")

    # Update invoice
    invoice.status = "rejected"
    invoice.rejection_reason = rejection.rejection_reason

    db.commit()
    db.refresh(invoice)

    # Create audit log
    audit_log = AuditLog(
        action="reject",
        entity_type="invoice",
        entity_id=invoice.id,
        user=rejection.rejected_by,
        new_values={
            "status": "rejected",
            "rejection_reason": rejection.rejection_reason,
        },
        description=f"Invoice rejected by {rejection.rejected_by}: {rejection.rejection_reason}",
    )
    db.add(audit_log)
    db.commit()

    return invoice


def _delete_invoice_file(file_path_str: str) -> None:
    """Delete the physical invoice file from disk. Logs but does not raise on failure."""
    try:
        p = Path(file_path_str)
        if p.exists():
            p.unlink()
            logger.info(f"Deleted file: {p}")
        else:
            logger.warning(f"File not found during deletion (already gone?): {p}")
    except Exception as e:
        logger.error(f"Could not delete file {file_path_str}: {e}")


@router.delete("/bulk")
async def delete_all_invoices(db: Session = Depends(get_db)):
    """Delete all invoices and their files"""

    invoices = db.query(Invoice).all()
    count = len(invoices)

    if count == 0:
        return {"message": "No invoices to delete", "deleted_count": 0}

    # Collect file paths before DB deletion
    file_paths = [inv.file_path for inv in invoices if inv.file_path]

    # Create audit log
    audit_log = AuditLog(
        action="bulk_delete",
        entity_type="invoice",
        entity_id=None,
        description=f"Bulk delete: {count} invoices deleted",
    )
    db.add(audit_log)

    # Delete DB records
    db.query(Invoice).delete()
    db.commit()

    # Delete files after successful DB commit
    for fp in file_paths:
        _delete_invoice_file(fp)

    logger.info(f"Bulk delete: {count} invoices and their files deleted")

    return {"message": f"{count} invoices deleted successfully", "deleted_count": count}


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Delete an invoice and its file"""

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    file_path = invoice.file_path

    # Create audit log before deletion
    audit_log = AuditLog(
        action="delete",
        entity_type="invoice",
        entity_id=invoice.id,
        old_values={
            "filename": invoice.filename,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "file_path": file_path,
        },
        description=f"Invoice deleted: {invoice.filename}",
    )
    db.add(audit_log)

    db.delete(invoice)
    db.commit()

    # Delete file after successful DB commit
    _delete_invoice_file(file_path)

    return {"message": "Invoice deleted successfully"}


@router.post("/process", response_model=InvoiceSchema)
async def process_invoice(
    request: InvoiceProcess,
    db: Session = Depends(get_db),
):
    """
    Register an invoice file that was already saved to disk (called by file-watcher).

    The file must already exist at the given file_path (inside /data/).
    Parses the file and creates a pending invoice record.
    """
    file_path = Path(request.file_path)

    if not file_path.exists():
        raise HTTPException(status_code=400, detail=f"File not found: {file_path}")

    # Parse invoice data
    extraction_status = "not_attempted"
    extraction_errors = []
    extracted_data = None

    try:
        logger.info(f"[process] Parsing file: {file_path}")
        extracted_data = InvoiceParser.parse_invoice(file_path)
        extraction_errors = extracted_data.extraction_errors

        if not extraction_errors:
            extraction_status = "success"
        elif extracted_data.invoice_number or extracted_data.amount_gross:
            extraction_status = "partial"
        else:
            extraction_status = "failed"
    except Exception as e:
        logger.error(f"[process] Extraction failed for {file_path}: {e}")
        extraction_errors.append(str(e))
        extraction_status = "failed"

    # Build invoice record
    invoice_data = {
        "filename": request.filename,
        "file_path": str(file_path),
        "invoice_type": request.invoice_type,
        "status": "pending",
    }

    if extracted_data and extraction_status in ("success", "partial"):
        for field in ("invoice_number", "invoice_date", "supplier_name", "supplier_id",
                      "supplier_email", "supplier_electronic_address",
                      "amount_net", "amount_gross", "amount_vat", "currency", "due_date"):
            value = getattr(extracted_data, field, None)
            if value is not None:
                invoice_data[field] = value

    db_invoice = Invoice(**invoice_data)
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    # Audit log
    audit_log = AuditLog(
        action="imported",
        entity_type="invoice",
        entity_id=db_invoice.id,
        new_values={
            "filename": request.filename,
            "file_path": str(file_path),
            "extraction_status": extraction_status,
            "extraction_errors": extraction_errors or None,
        },
        description=f"Invoice imported by file-watcher: {request.filename} (extraction: {extraction_status})",
    )
    db.add(audit_log)
    db.commit()

    logger.info(
        f"[process] Invoice created: id={db_invoice.id}, file={request.filename}, "
        f"extraction={extraction_status}"
    )
    return db_invoice


@router.post("/upload", response_model=InvoiceSchema)
async def upload_invoice(
    file: UploadFile = File(...),
    auto_extract: bool = Form(True),
    invoice_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload invoice file (ZUGFeRD PDF or XRechnung XML) with automatic data extraction

    Args:
        file: PDF or XML file
        auto_extract: Whether to automatically extract invoice data (default: True)
        invoice_type: Invoice type (incoming/outgoing/credit_note)

    Returns:
        Created invoice with extraction metadata
    """

    # Validate file
    is_valid, error_msg = await FileService.validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Save file to PROCESSING_PATH
    try:
        saved_path = await FileService.save_uploaded_file(file, settings.PROCESSING_PATH)
    except IOError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Extract data if auto_extract is True
    extracted_data = None
    extraction_errors = []
    extraction_status = "not_attempted"

    if auto_extract:
        try:
            logger.info(f"Extracting data from {saved_path}")
            extracted_data = InvoiceParser.parse_invoice(saved_path)
            extraction_errors = extracted_data.extraction_errors

            if not extraction_errors:
                extraction_status = "success"
            elif extracted_data.invoice_number or extracted_data.amount_gross:
                # Partial extraction - some data was extracted
                extraction_status = "partial"
            else:
                extraction_status = "failed"

        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            extraction_errors.append(f"Extraction failed: {str(e)}")
            extraction_status = "failed"

    # Create invoice record
    invoice_data = {
        "filename": file.filename,
        "file_path": str(saved_path),
        "invoice_type": invoice_type or "incoming",
        "status": "pending",
    }

    # Merge extracted data if available
    if extracted_data and extraction_status in ["success", "partial"]:
        if extracted_data.invoice_number:
            invoice_data["invoice_number"] = extracted_data.invoice_number
        if extracted_data.invoice_date:
            invoice_data["invoice_date"] = extracted_data.invoice_date
        if extracted_data.supplier_name:
            invoice_data["supplier_name"] = extracted_data.supplier_name
        if extracted_data.supplier_id:
            invoice_data["supplier_id"] = extracted_data.supplier_id
        if extracted_data.supplier_email:
            invoice_data["supplier_email"] = extracted_data.supplier_email
        if extracted_data.supplier_electronic_address:
            invoice_data["supplier_electronic_address"] = extracted_data.supplier_electronic_address
        if extracted_data.amount_net:
            invoice_data["amount_net"] = extracted_data.amount_net
        if extracted_data.amount_gross:
            invoice_data["amount_gross"] = extracted_data.amount_gross
        if extracted_data.amount_vat:
            invoice_data["amount_vat"] = extracted_data.amount_vat
        if extracted_data.currency:
            invoice_data["currency"] = extracted_data.currency
        if extracted_data.due_date:
            invoice_data["due_date"] = extracted_data.due_date

    # Create database record
    db_invoice = Invoice(**invoice_data)
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    # Create audit log (convert datetime and Decimal objects to strings for JSON serialization)
    audit_values = {}
    for key, value in invoice_data.items():
        if isinstance(value, datetime):
            audit_values[key] = value.isoformat() if value else None
        elif isinstance(value, Decimal):
            audit_values[key] = float(value) if value else None
        else:
            audit_values[key] = value

    audit_log = AuditLog(
        action="upload",
        entity_type="invoice",
        entity_id=db_invoice.id,
        new_values={
            **audit_values,
            "extraction_status": extraction_status,
            "extraction_errors": extraction_errors if extraction_errors else None,
        },
        description=f"Invoice uploaded: {file.filename} (extraction: {extraction_status})",
    )
    db.add(audit_log)
    db.commit()

    logger.info(
        f"Invoice created: ID={db_invoice.id}, file={file.filename}, "
        f"extraction={extraction_status}"
    )

    return db_invoice


@router.get("/{invoice_id}/file")
async def get_invoice_file(
    invoice_id: int,
    disposition: str = Query("inline", regex="^(inline|attachment)$"),
    db: Session = Depends(get_db),
):
    """
    Download or preview invoice file

    Args:
        invoice_id: Invoice ID
        disposition: 'inline' for preview, 'attachment' for download

    Returns:
        File response with PDF or XML content
    """
    # Get invoice from database
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get file path
    file_path = Path(invoice.file_path)

    # Validate file exists
    if not file_path.exists():
        logger.error(f"File not found: {file_path} for invoice {invoice_id}")
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {invoice.filename}"
        )

    # Validate file is within allowed data directory (security check)
    try:
        file_path_resolved = file_path.resolve()
        data_path_resolved = settings.DATA_PATH.resolve()

        if not str(file_path_resolved).startswith(str(data_path_resolved)):
            logger.error(
                f"Security: Attempted access to file outside data directory: {file_path}"
            )
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error(f"Error validating file path: {e}")
        raise HTTPException(status_code=500, detail="File path validation error")

    # Determine content type
    content_type = "application/pdf" if file_path.suffix == ".pdf" else "application/xml"

    # Return file
    return FileResponse(
        path=file_path,
        media_type=content_type,
        headers={
            "Content-Disposition": f'{disposition}; filename="{invoice.filename}"'
        },
        filename=invoice.filename,
    )
