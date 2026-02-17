from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    """Audit log for tracking changes and actions"""

    __tablename__ = "audit_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Action details
    action = Column(String(50), nullable=False, index=True)  # e.g., "approve", "reject", "export", "update"
    entity_type = Column(String(50), nullable=False)  # e.g., "invoice"
    entity_id = Column(Integer, nullable=True, index=True)  # Nullable for bulk operations

    # User information
    user = Column(String(100))  # Username or email
    ip_address = Column(String(45))  # IPv4 or IPv6

    # Change details
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    description = Column(Text)  # Human-readable description

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} on {self.entity_type} {self.entity_id}>"
