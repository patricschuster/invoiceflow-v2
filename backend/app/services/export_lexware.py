import shutil
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)


class LexwareExporter:
    """Exports approved invoices to Lexware-compatible format (PDF + JSON)."""

    def __init__(self):
        self.export_path = settings.EXPORT_ACCOUNTING_PATH

    def export(self, invoice) -> dict:
        """
        Export invoice to accounting folder.

        Returns:
            dict with keys: success, pdf_path, json_path, error (on failure)
        """
        try:
            # 1. Monats-Ordner anlegen: {export_path}/YYYY-MM/
            ref_date = invoice.invoice_date or invoice.approved_at or datetime.now(timezone.utc)
            if hasattr(ref_date, 'year'):
                month_folder = self.export_path / f"{ref_date.year}-{ref_date.month:02d}"
            else:
                now = datetime.now(timezone.utc)
                month_folder = self.export_path / f"{now.year}-{now.month:02d}"

            month_folder.mkdir(parents=True, exist_ok=True)

            # 2. base_name = '{invoice_number}_{supplier_name}'.replace(' ', '_')
            invoice_number = invoice.invoice_number or f"INV-{invoice.id}"
            supplier_name = invoice.supplier_name or "Unbekannt"
            base_name = f"{invoice_number}_{supplier_name}".replace(" ", "_")

            # 3. PDF kopieren
            source_path = Path(invoice.file_path)
            pdf_dest = month_folder / f"{base_name}.pdf"

            if source_path.exists():
                shutil.copy2(source_path, pdf_dest)
            else:
                logger.warning(f"Source file not found: {source_path}, skipping PDF copy")
                pdf_dest = None

            # 4. JSON schreiben
            json_dest = month_folder / f"{base_name}.json"
            export_data = {
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "supplier_name": invoice.supplier_name,
                "supplier_id": invoice.supplier_id,
                "amount_net": float(invoice.amount_net) if invoice.amount_net is not None else None,
                "amount_gross": float(invoice.amount_gross) if invoice.amount_gross is not None else None,
                "amount_vat": float(invoice.amount_vat) if invoice.amount_vat is not None else None,
                "currency": invoice.currency,
                "cost_center": invoice.cost_center,
                "project": invoice.project,
                "tags": invoice.tags,
                "approved_by": invoice.approved_by,
                "approved_at": invoice.approved_at.isoformat() if invoice.approved_at else None,
                "dms_url": invoice.dms_url,
                "invoice_type": invoice.invoice_type,
                "export_date": datetime.now(timezone.utc).isoformat(),
            }

            with open(json_dest, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Lexware export successful: {json_dest}")

            return {
                "success": True,
                "pdf_path": str(pdf_dest) if pdf_dest else None,
                "json_path": str(json_dest),
            }

        except Exception as e:
            logger.error(f"Lexware export failed for invoice {invoice.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "pdf_path": None,
                "json_path": None,
            }
