import shutil
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

import requests

from app.config import settings

logger = logging.getLogger(__name__)


def _get_paperless_setting(key: str, fallback: str) -> str:
    """Read a setting from DB, fall back to env var."""
    try:
        from app.database import SessionLocal
        from app.models.setting import Setting
        with SessionLocal() as db:
            row = db.query(Setting).filter(Setting.key == key).first()
            return (row.value or fallback) if row else fallback
    except Exception:
        return fallback


class PaperlessExporter:
    """Exports approved invoices to Paperless-ngx via API or consumption folder."""

    def __init__(self):
        self.paperless_url = _get_paperless_setting("PAPERLESS_URL", settings.PAPERLESS_URL).rstrip("/")
        self.paperless_token = _get_paperless_setting("PAPERLESS_TOKEN", settings.PAPERLESS_TOKEN or "")
        self.dms_path = settings.EXPORT_DMS_PATH

    def export(self, invoice) -> dict:
        """
        Export invoice to Paperless-ngx.

        Uses API if token is configured, otherwise falls back to folder export.

        Returns:
            dict with keys: success, dms_url (optional), error (on failure)
        """
        if self.paperless_token and self.paperless_token.strip():
            return self._export_via_api(invoice)
        else:
            return self._export_via_folder(invoice)

    def _get_or_create_correspondent(self, name: str, headers: dict) -> int | None:
        """Look up correspondent by name in Paperless, create if not found. Returns integer ID or None."""
        try:
            # Paperless uses 'name' as a contains-filter; we check for exact match afterwards
            resp = requests.get(
                f"{self.paperless_url}/api/correspondents/",
                headers=headers,
                params={"name": name},
                timeout=10,
            )
            logger.info(f"Correspondent GET status={resp.status_code}, body={resp.text[:200]}")

            if resp.status_code == 200:
                results = resp.json().get("results", [])
                for c in results:
                    if c.get("name", "").lower() == name.lower():
                        logger.info(f"Found existing correspondent '{name}' with id={c['id']}")
                        return c["id"]

            # Not found – create new correspondent
            logger.info(f"Correspondent '{name}' not found, creating...")
            resp = requests.post(
                f"{self.paperless_url}/api/correspondents/",
                headers={**headers, "Content-Type": "application/json"},
                json={"name": name},
                timeout=10,
            )
            logger.info(f"Correspondent POST status={resp.status_code}, body={resp.text[:200]}")
            if resp.status_code in (200, 201):
                new_id = resp.json().get("id")
                logger.info(f"Created correspondent '{name}' with id={new_id}")
                return new_id

            logger.warning(f"Could not create correspondent '{name}': {resp.status_code} {resp.text}")
            return None
        except Exception as e:
            logger.warning(f"Correspondent lookup/create failed for '{name}': {e}")
            return None

    def _get_or_create_custom_field(self, field_name: str, headers: dict) -> int | None:
        """Look up a Paperless custom field by name, create if not found. Returns integer ID or None."""
        try:
            resp = requests.get(
                f"{self.paperless_url}/api/custom_fields/",
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 200:
                for field in resp.json().get("results", []):
                    if field.get("name", "").lower() == field_name.lower():
                        logger.info(f"Found existing custom field '{field_name}' with id={field['id']}")
                        return field["id"]

            # Not found – create as string field
            resp = requests.post(
                f"{self.paperless_url}/api/custom_fields/",
                headers={**headers, "Content-Type": "application/json"},
                json={"name": field_name, "data_type": "string"},
                timeout=10,
            )
            if resp.status_code in (200, 201):
                new_id = resp.json().get("id")
                logger.info(f"Created custom field '{field_name}' with id={new_id}")
                return new_id

            logger.warning(f"Could not create custom field '{field_name}': {resp.status_code} {resp.text[:200]}")
            return None
        except Exception as e:
            logger.warning(f"Custom field lookup/create failed for '{field_name}': {e}")
            return None

    def _export_via_api(self, invoice) -> dict:
        """Upload document directly to Paperless-ngx via REST API."""
        try:
            source_path = Path(invoice.file_path)
            if not source_path.exists():
                return {"success": False, "error": f"Source file not found: {source_path}"}

            supplier = invoice.supplier_name or "Unbekannt"
            invoice_number = invoice.invoice_number or f"INV-{invoice.id}"
            title = f"{invoice_number} - {supplier}"

            # Format date as YYYY-MM-DD (Paperless Ausstellungsdatum / created)
            created = None
            if invoice.invoice_date:
                d = invoice.invoice_date
                # works for both date and datetime objects
                created = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]

            logger.info(
                f"Exporting invoice {invoice.id}: supplier='{supplier}', "
                f"invoice_date={invoice.invoice_date!r}, created='{created}'"
            )

            headers = {"Authorization": f"Token {self.paperless_token}"}

            data = {"title": title}
            if created:
                data["created"] = created

            # Resolve correspondent ID from supplier name
            if invoice.supplier_name:
                correspondent_id = self._get_or_create_correspondent(invoice.supplier_name, headers)
                if correspondent_id:
                    data["correspondent"] = correspondent_id
                    logger.info(f"Using correspondent id={correspondent_id} for '{invoice.supplier_name}'")
                else:
                    logger.warning(f"No correspondent id resolved for '{invoice.supplier_name}' – field will be empty")

            # Set custom field "Freigegeben von" with the approving user's name
            if invoice.approved_by:
                cf_id = self._get_or_create_custom_field("Freigegeben von", headers)
                if cf_id:
                    import json as _json
                    # Paperless post_document expects: {"<field_id>": "<value>"}
                    data["custom_fields"] = _json.dumps({str(cf_id): invoice.approved_by})
                    logger.info(f"Setting custom field 'Freigegeben von' = '{invoice.approved_by}' (id={cf_id})")

            logger.info(f"post_document data fields: {list(data.keys())}, values: { {k: v for k, v in data.items() if k != 'document'} }")

            with open(source_path, "rb") as f:
                response = requests.post(
                    f"{self.paperless_url}/api/documents/post_document/",
                    headers=headers,
                    data=data,
                    files={"document": (source_path.name, f, "application/pdf")},
                    timeout=30,
                )

            if response.status_code in (200, 201):
                doc_id = response.json() if response.text.strip().isdigit() else None
                dms_url = f"{self.paperless_url}/documents/{doc_id}" if doc_id else self.paperless_url
                logger.info(f"Paperless API export successful: {dms_url}")
                return {"success": True, "dms_url": dms_url}
            else:
                logger.error(f"Paperless API error {response.status_code}: {response.text}")
                return {"success": False, "error": f"API error {response.status_code}: {response.text}"}

        except Exception as e:
            logger.error(f"Paperless API export failed for invoice {invoice.id}: {e}")
            return {"success": False, "error": str(e)}

    def _export_via_folder(self, invoice) -> dict:
        """Copy document to DMS consumption folder with sidecar JSON."""
        try:
            self.dms_path.mkdir(parents=True, exist_ok=True)

            source_path = Path(invoice.file_path)
            if not source_path.exists():
                return {"success": False, "error": f"Source file not found: {source_path}"}

            supplier = invoice.supplier_name or "Unbekannt"
            cost_center = invoice.cost_center or "kein-kc"
            invoice_number = invoice.invoice_number or f"INV-{invoice.id}"

            # Tags im Dateinamen
            filename = f"Freigegeben,{supplier},{cost_center}_{invoice_number}.pdf"
            filename = filename.replace(" ", "_")
            dest_path = self.dms_path / filename

            shutil.copy2(source_path, dest_path)

            # Sidecar-JSON
            tags = invoice.tags or []
            if isinstance(tags, str):
                tags = [tags]

            sidecar = {
                "title": f"{invoice_number} - {supplier}",
                "correspondent": supplier,
                "document_type": "Rechnung",
                "created": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "tags": tags,
            }
            sidecar_path = self.dms_path / f"{dest_path.stem}.json"
            with open(sidecar_path, "w", encoding="utf-8") as f:
                json.dump(sidecar, f, ensure_ascii=False, indent=2)

            logger.info(f"Paperless folder export successful: {dest_path}")
            return {"success": True, "dms_url": None}

        except Exception as e:
            logger.error(f"Paperless folder export failed for invoice {invoice.id}: {e}")
            return {"success": False, "error": str(e)}
