"""SQLAlchemy model for Victims (Anonymized)."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Victim(Base):
    """
    Victim model storing anonymized case records.
    
    IMPORTANT PRIVACY CONSTRAINT:
    - Only anonymized/pseudonymized IDs (e.g. VIC-2024-0821) are stored.
    - Real names or PII are strictly disallowed in accordance with project rules.
    """
    __tablename__ = "victims"

    id = Column(String(50), primary_key=True, index=True)  # Anonymized identifier: e.g. VIC-2024-001
    case_type = Column(String(100), nullable=False, index=True)  # e.g., "atrocity_act", "intimidation", "sexual_violence"
    registration_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    assigned_district = Column(String(100), nullable=False, index=True)
    assigned_state = Column(String(100), nullable=False, index=True)
    
    # Cached metrics from latest ML evaluation
    current_distress_score = Column(Float, default=0.0)
    current_trend = Column(String(50), default="stable")  # improving, stable, worsening
    escalation_probability = Column(Float, default=0.0)
    risk_level = Column(String(50), default="low")  # low, moderate, high

    # Privacy & Case state
    consent_flag = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default="active")  # active, monitoring, closed
    
    assigned_counsellor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    check_ins = relationship("CheckIn", back_populates="victim", cascade="all, delete-orphan", order_by="CheckIn.timestamp.desc()")
    alerts = relationship("Alert", back_populates="victim", cascade="all, delete-orphan", order_by="Alert.triggered_at.desc()")
    assigned_counsellor = relationship("User", foreign_keys=[assigned_counsellor_id])
