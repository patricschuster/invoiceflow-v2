#!/usr/bin/env python3
"""
Test script to debug ZUGFeRD parsing
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.invoice_parser import InvoiceParser
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_parse_pdf(pdf_path: str):
    """Test parsing a PDF file"""
    print(f"\n{'='*60}")
    print(f"Testing ZUGFeRD parser with: {pdf_path}")
    print(f"{'='*60}\n")

    path = Path(pdf_path)
    if not path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        return

    print(f"File exists: {path}")
    print(f"File size: {path.stat().st_size} bytes\n")

    # Parse the invoice
    print("Starting parse...")
    invoice_data = InvoiceParser.parse_invoice(path)

    # Print results
    print(f"\n{'='*60}")
    print("PARSING RESULTS:")
    print(f"{'='*60}")
    print(f"Detected format: {invoice_data.detected_format}")
    print(f"Invoice number: {invoice_data.invoice_number}")
    print(f"Invoice date: {invoice_data.invoice_date}")
    print(f"Supplier name: {invoice_data.supplier_name}")
    print(f"Supplier ID: {invoice_data.supplier_id}")
    print(f"Amount net: {invoice_data.amount_net}")
    print(f"Amount gross: {invoice_data.amount_gross}")
    print(f"Amount VAT: {invoice_data.amount_vat}")
    print(f"Currency: {invoice_data.currency}")
    print(f"Due date: {invoice_data.due_date}")

    if invoice_data.extraction_errors:
        print(f"\nERRORS ({len(invoice_data.extraction_errors)}):")
        for error in invoice_data.extraction_errors:
            print(f"  - {error}")

    if invoice_data.extraction_warnings:
        print(f"\nWARNINGS ({len(invoice_data.extraction_warnings)}):")
        for warning in invoice_data.extraction_warnings:
            print(f"  - {warning}")

    if invoice_data.raw_xml:
        print(f"\nXML length: {len(invoice_data.raw_xml)} characters")
        print(f"First 500 chars of XML:")
        print(invoice_data.raw_xml[:500])

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_parser.py <path_to_zugferd_pdf>")
        print("\nLooking for uploaded files...")

        # Try to find uploaded files
        data_paths = [
            Path("/app/data/processing"),
            Path("/app/data/incoming"),
        ]

        for data_path in data_paths:
            if data_path.exists():
                print(f"\nFiles in {data_path}:")
                for file in data_path.glob("*.pdf"):
                    print(f"  - {file}")

        sys.exit(1)

    pdf_path = sys.argv[1]
    test_parse_pdf(pdf_path)
