"""
Script to seed the database with sample invoice data
Run this after starting the Docker containers
"""

import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, engine, Base
from app.models.invoice import Invoice
from app.models.audit_log import AuditLog

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def create_sample_invoices():
    """Create sample invoices for testing"""

    db = SessionLocal()

    try:
        # Check if data already exists
        count = db.query(Invoice).count()
        if count > 0:
            print(f"Database already contains {count} invoices. Skipping seed.")
            return

        # Sample invoices
        sample_invoices = [
            {
                "filename": "rechnung_acme_corp_2024_001.pdf",
                "file_path": "/app/data/incoming/rechnung_acme_corp_2024_001.pdf",
                "invoice_type": "incoming",
                "invoice_number": "RE-2024-001",
                "invoice_date": datetime.now() - timedelta(days=10),
                "supplier_name": "Acme Corporation GmbH",
                "supplier_id": "DE123456789",
                "amount_net": Decimal("1000.00"),
                "amount_gross": Decimal("1190.00"),
                "amount_vat": Decimal("190.00"),
                "currency": "EUR",
                "due_date": datetime.now() + timedelta(days=20),
                "tags": ["office", "hardware"],
                "cost_center": None,
                "project": None,
                "comment": None,
                "status": "pending",
            },
            {
                "filename": "rechnung_techsupply_2024_042.pdf",
                "file_path": "/app/data/incoming/rechnung_techsupply_2024_042.pdf",
                "invoice_type": "incoming",
                "invoice_number": "TS-2024-042",
                "invoice_date": datetime.now() - timedelta(days=5),
                "supplier_name": "TechSupply Deutschland AG",
                "supplier_id": "DE987654321",
                "amount_net": Decimal("2500.00"),
                "amount_gross": Decimal("2975.00"),
                "amount_vat": Decimal("475.00"),
                "currency": "EUR",
                "due_date": datetime.now() + timedelta(days=25),
                "tags": ["it", "software"],
                "cost_center": "KST-IT",
                "project": "PROJ-2024-DIGITAL",
                "comment": "Software-Lizenzen für Q1 2024",
                "status": "approved",
                "approved_by": "admin",
                "approved_at": datetime.now() - timedelta(days=2),
            },
            {
                "filename": "rechnung_office_world_2024_789.pdf",
                "file_path": "/app/data/incoming/rechnung_office_world_2024_789.pdf",
                "invoice_type": "incoming",
                "invoice_number": "OW-789-2024",
                "invoice_date": datetime.now() - timedelta(days=15),
                "supplier_name": "Office World GmbH & Co. KG",
                "supplier_id": "DE555777999",
                "amount_net": Decimal("450.50"),
                "amount_gross": Decimal("536.10"),
                "amount_vat": Decimal("85.60"),
                "currency": "EUR",
                "due_date": datetime.now() + timedelta(days=15),
                "tags": ["office", "supplies"],
                "cost_center": "KST-ADMIN",
                "project": None,
                "comment": None,
                "status": "pending",
            },
            {
                "filename": "rechnung_consulting_partners_2024_123.pdf",
                "file_path": "/app/data/incoming/rechnung_consulting_partners_2024_123.pdf",
                "invoice_type": "incoming",
                "invoice_number": "CP-2024-123",
                "invoice_date": datetime.now() - timedelta(days=20),
                "supplier_name": "Consulting Partners International",
                "supplier_id": "DE111222333",
                "amount_net": Decimal("8500.00"),
                "amount_gross": Decimal("10115.00"),
                "amount_vat": Decimal("1615.00"),
                "currency": "EUR",
                "due_date": datetime.now() + timedelta(days=10),
                "tags": ["consulting", "urgent"],
                "cost_center": "KST-MGMT",
                "project": "PROJ-2024-STRATEGY",
                "comment": "Strategieberatung Q1",
                "status": "approved",
                "approved_by": "manager",
                "approved_at": datetime.now() - timedelta(days=5),
            },
            {
                "filename": "rechnung_facilities_service_2024_055.pdf",
                "file_path": "/app/data/incoming/rechnung_facilities_service_2024_055.pdf",
                "invoice_type": "incoming",
                "invoice_number": "FS-055-2024",
                "invoice_date": datetime.now() - timedelta(days=8),
                "supplier_name": "Facilities Service München",
                "supplier_id": "DE444555666",
                "amount_net": Decimal("750.00"),
                "amount_gross": Decimal("892.50"),
                "amount_vat": Decimal("142.50"),
                "currency": "EUR",
                "due_date": datetime.now() + timedelta(days=22),
                "tags": ["facilities", "maintenance"],
                "cost_center": "KST-FACILITIES",
                "project": None,
                "comment": "Monatliche Wartung",
                "status": "rejected",
                "rejection_reason": "Rechnung enthält falsche Leistungszeiträume. Bitte korrigieren und erneut einreichen.",
            },
            {
                "filename": "rechnung_cloud_services_2024_999.pdf",
                "file_path": "/app/data/incoming/rechnung_cloud_services_2024_999.pdf",
                "invoice_type": "incoming",
                "invoice_number": "CS-999-JAN24",
                "invoice_date": datetime.now() - timedelta(days=3),
                "supplier_name": "Cloud Services Europe B.V.",
                "supplier_id": "NL123456789B01",
                "amount_net": Decimal("3200.00"),
                "amount_gross": Decimal("3808.00"),
                "amount_vat": Decimal("608.00"),
                "currency": "EUR",
                "due_date": datetime.now() + timedelta(days=27),
                "tags": ["it", "cloud", "recurring"],
                "cost_center": "KST-IT",
                "project": None,
                "comment": None,
                "status": "pending",
            },
            {
                "filename": "rechnung_marketing_agency_2024_012.pdf",
                "file_path": "/app/data/incoming/rechnung_marketing_agency_2024_012.pdf",
                "invoice_type": "incoming",
                "invoice_number": "MA-012-2024",
                "invoice_date": datetime.now() - timedelta(days=12),
                "supplier_name": "Creative Marketing Agency GmbH",
                "supplier_id": "DE888999000",
                "amount_net": Decimal("5600.00"),
                "amount_gross": Decimal("6664.00"),
                "amount_vat": Decimal("1064.00"),
                "currency": "EUR",
                "due_date": datetime.now() + timedelta(days=18),
                "tags": ["marketing", "campaign"],
                "cost_center": "KST-MARKETING",
                "project": "PROJ-2024-LAUNCH",
                "comment": "Kampagne für Produktlaunch",
                "status": "approved",
                "approved_by": "marketing_lead",
                "approved_at": datetime.now() - timedelta(days=1),
            },
            {
                "filename": "rechnung_energy_provider_2024_jan.pdf",
                "file_path": "/app/data/incoming/rechnung_energy_provider_2024_jan.pdf",
                "invoice_type": "incoming",
                "invoice_number": "EP-JAN-2024-99887",
                "invoice_date": datetime.now() - timedelta(days=6),
                "supplier_name": "Stadtwerke München GmbH",
                "supplier_id": "DE777888999",
                "amount_net": Decimal("1250.00"),
                "amount_gross": Decimal("1487.50"),
                "amount_vat": Decimal("237.50"),
                "currency": "EUR",
                "due_date": datetime.now() + timedelta(days=24),
                "tags": ["utilities", "energy"],
                "cost_center": "KST-FACILITIES",
                "project": None,
                "comment": "Stromrechnung Januar 2024",
                "status": "pending",
            },
        ]

        # Insert invoices
        created_invoices = []
        for invoice_data in sample_invoices:
            invoice = Invoice(**invoice_data)
            db.add(invoice)
            created_invoices.append(invoice)

        db.commit()

        # Create audit logs for created invoices
        for invoice in created_invoices:
            db.refresh(invoice)
            audit_log = AuditLog(
                action="create",
                entity_type="invoice",
                entity_id=invoice.id,
                user="system",
                new_values={"filename": invoice.filename, "status": invoice.status},
                description=f"Sample invoice created: {invoice.filename}",
            )
            db.add(audit_log)

        db.commit()

        print(f"✅ Successfully created {len(sample_invoices)} sample invoices!")
        print("\nSample invoices:")
        for invoice in created_invoices:
            status_icon = "⏳" if invoice.status == "pending" else "✅" if invoice.status == "approved" else "❌"
            print(f"  {status_icon} {invoice.invoice_number} - {invoice.supplier_name} - {invoice.amount_gross} EUR ({invoice.status})")

    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding database with sample invoices...\n")
    create_sample_invoices()
    print("\n✨ Done! You can now access the invoices at http://localhost:3000")
