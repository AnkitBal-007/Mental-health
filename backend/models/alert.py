"""SQLAlchemy model for Alerts."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class Alert(Base):
    """
    Alert record triggered when distress scores or escalation probabilities
    cross safety thresholds. Routed to counsellor/official work queues.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    victim_id = Column(String(50), ForeignKey("victims.id"), nullable=False, index=True)
    triggered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    risk_level = Column(String(50), nullable=False, default="high")  # moderate, high, critical
    status = Column(String(50), nullable=False, default="open")      # open, assigned, under_review, resolved, dismissed
    
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)  # Counsellor or official user ID
    
    # Snapshot metrics when alert triggered
    distress_score = Column(Float, nullable=False, default=0.0)
    escalation_probability = Column(Float, nullable=False, default=0.0)
    
    trigger_reason = Column(Text, nullable=False)
    explanation_factors = Column(Text, nullable=True)  # JSON-encoded factor breakdown
    recommended_actions = Column(Text, nullable=True)  # JSON-encoded recommended interventions
    
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    victim = relationship("Victim", back_populates="alerts")
    assignee = relationship("User", foreign_keys=[assigned_to])
