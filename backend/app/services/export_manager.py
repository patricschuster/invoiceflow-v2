import logging
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.services.export_lexware import LexwareExporter
from app.services.export_paperless import PaperlessExporter

logger = logging.getLogger(__name__)


class ExportManager:
    """Orchestrates all export steps after invoice approval."""

    def __init__(self, db: Session):
        self.db = db
        self.lexware = LexwareExporter()
        self.paperless = PaperlessExporter()

    def export_invoice(self, invoice) -> dict:
        """
        Run all export steps for an approved invoice.

        Returns:
            dict with keys: accounting, dms, success
        """
        accounting_result = self._run_lexware(invoice)
        dms_result = self._run_paperless(invoice)

        self.db.commit()

        return {
            "accounting": accounting_result,
            "dms": dms_result,
            "success": accounting_result.get("success", False) and dms_result.get("success", False),
        }

    def _run_lexware(self, invoice) -> dict:
        result = self.lexware.export(invoice)

        invoice.exported_to_accounting = result["success"]

        audit_log = AuditLog(
            action="export_accounting",
            entity_type="invoice",
            entity_id=invoice.id,
            new_values={
                "success": result["success"],
                "pdf_path": result.get("pdf_path"),
                "json_path": result.get("json_path"),
                "error": result.get("error"),
            },
            description=(
                f"Lexware export {'successful' if result['success'] else 'failed'} "
                f"for invoice {invoice.id}"
            ),
        )
        self.db.add(audit_log)
        return result

    def _run_paperless(self, invoice) -> dict:
        result = self.paperless.export(invoice)

        invoice.exported_to_dms = result["success"]
        if result.get("dms_url"):
            invoice.dms_url = result["dms_url"]

        audit_log = AuditLog(
            action="export_dms",
            entity_type="invoice",
            entity_id=invoice.id,
            new_values={
                "success": result["success"],
                "dms_url": result.get("dms_url"),
                "error": result.get("error"),
            },
            description=(
                f"Paperless export {'successful' if result['success'] else 'failed'} "
                f"for invoice {invoice.id}"
            ),
        )
        self.db.add(audit_log)
        return result
