import logging
from pathlib import Path

import requests

from config import API_URL

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processes invoice files by sending them to the backend API."""

    ALLOWED_EXTENSIONS = {".pdf", ".xml"}

    @staticmethod
    def process(file_path: Path) -> dict:
        """
        Validate file and notify backend to create invoice record.

        Args:
            file_path: Path to the file in /data/processing/

        Returns:
            dict with invoice data from the API

        Raises:
            ValueError: If file is invalid
            RuntimeError: If API call fails
        """
        # Validate file exists
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        # Validate extension
        if file_path.suffix.lower() not in PDFProcessor.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # Validate not empty
        if file_path.stat().st_size == 0:
            raise ValueError(f"File is empty: {file_path}")

        # Determine invoice type based on extension
        invoice_type = "incoming"

        logger.info(f"Calling backend API to process: {file_path}")

        try:
            response = requests.post(
                f"{API_URL}/api/invoices/process",
                json={
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "invoice_type": invoice_type,
                },
                timeout=60,
            )
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Backend not reachable: {e}")
        except requests.exceptions.Timeout:
            raise RuntimeError("Backend API timed out")

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Backend returned {response.status_code}: {response.text[:200]}"
            )

        invoice = response.json()
        logger.info(
            f"Invoice created via process API: id={invoice.get('id')}, "
            f"number={invoice.get('invoice_number')}, supplier={invoice.get('supplier_name')}"
        )
        return invoice
