from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, JSON, Text
from sqlalchemy.sql import func
from app.database import Base


class Invoice(Base):
    """Invoice model"""

    __tablename__ = "invoices"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # File information
    filename = Column(String(255), nullable=False)           # disk name (with timestamp prefix)
    original_filename = Column(String(255), nullable=True)   # original name from incoming/
    file_path = Column(String(500), nullable=False)
    invoice_type = Column(String(50))  # e.g., "incoming", "outgoing", "credit_note"

    # Invoice data
    invoice_number = Column(String(100), index=True)
    invoice_date = Column(DateTime(timezone=True))
    supplier_name = Column(String(255))
    supplier_id = Column(String(100))  # Tax ID or vendor number
    supplier_email = Column(String(255))  # Contact email (DefinedTradeContact)
    supplier_electronic_address = Column(String(255))  # Electronic address / Peppol ID

    # Amounts
    amount_net = Column(Numeric(10, 2))
    amount_gross = Column(Numeric(10, 2))
    amount_vat = Column(Numeric(10, 2))
    currency = Column(String(3), default="EUR")  # ISO 4217 currency code
    due_date = Column(DateTime(timezone=True))

    # Organization
    tags = Column(JSON)  # Array of tags as JSON
    cost_center = Column(String(100))
    project = Column(String(100))
    comment = Column(Text)

    # Approval workflow
    status = Column(String(20), default="pending", index=True)  # pending, approved, rejected
    rejection_reason = Column(Text)
    approved_by = Column(String(100))
    approved_at = Column(DateTime(timezone=True))

    # Export tracking
    exported_to_accounting = Column(Boolean, default=False)
    exported_to_dms = Column(Boolean, default=False)
    dms_url = Column(String(500))

    # Processing metadata (used by file-watcher)
    processing_error = Column(Text, nullable=True)
    processing_attempts = Column(Integer, default=0)

    # Email archiving
    email_archived_path = Column(String(500))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Invoice {self.id}: {self.invoice_number} - {self.supplier_name}>"
