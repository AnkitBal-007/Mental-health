"""SQLAlchemy model for Audit Logs."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from database import Base


class AuditLog(Base):
    """
    Audit log record tracking access and actions performed on victim records.
    Ensures privacy compliance and accountable governance.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(100), nullable=True)
    role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., "VIEW_VICTIM_DETAIL", "EVALUATE_ALERT", "ASSIGN_ALERT"
    target_victim_id = Column(String(50), nullable=True, index=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
