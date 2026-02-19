from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class InvoiceBase(BaseModel):
    """Base invoice schema"""
    filename: str
    invoice_type: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    supplier_name: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_email: Optional[str] = None
    supplier_electronic_address: Optional[str] = None
    amount_net: Optional[Decimal] = None
    amount_gross: Optional[Decimal] = None
    amount_vat: Optional[Decimal] = None
    currency: str = "EUR"
    due_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    cost_center: Optional[str] = None
    project: Optional[str] = None
    comment: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice"""
    file_path: str


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice"""
    invoice_type: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    supplier_name: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_email: Optional[str] = None
    supplier_electronic_address: Optional[str] = None
    amount_net: Optional[Decimal] = None
    amount_gross: Optional[Decimal] = None
    amount_vat: Optional[Decimal] = None
    currency: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    cost_center: Optional[str] = None
    project: Optional[str] = None
    comment: Optional[str] = None


class InvoiceApprove(BaseModel):
    """Schema for approving an invoice"""
    approved_by: str
    cost_center: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[list[str]] = None
    comment: Optional[str] = None


class InvoiceReject(BaseModel):
    """Schema for rejecting an invoice"""
    rejection_reason: str
    rejected_by: str


class InvoiceProcess(BaseModel):
    """Schema for file-watcher process request"""
    filename: str                          # disk name (with timestamp prefix)
    original_filename: Optional[str] = None  # original name from incoming/
    file_path: str
    invoice_type: str = "incoming"


class Invoice(InvoiceBase):
    """Complete invoice schema"""
    id: int
    file_path: str
    original_filename: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    exported_to_accounting: bool
    exported_to_dms: bool
    dms_url: Optional[str] = None
    processing_error: Optional[str] = None
    processing_attempts: int = 0
    email_archived_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceStats(BaseModel):
    """Statistics about invoices"""
    total: int
    pending: int
    approved: int
    rejected: int
    total_amount_pending: Decimal
    total_amount_approved: Decimal
