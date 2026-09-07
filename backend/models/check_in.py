"""SQLAlchemy model for Check-ins."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class CheckIn(Base):
    """
    CheckIn model representing a victim interaction across any channel
    (Chatbot, IVRS, SMS, Web Portal).
    """
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    victim_id = Column(String(50), ForeignKey("victims.id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False, default="chatbot")  # chatbot, ivrs, sms, portal
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # NLP & Acoustic Analysis results
    sentiment_score = Column(Float, nullable=False, default=0.0)  # -1.0 to 1.0
    emotion_label = Column(String(50), nullable=False, default="neutral")  # fear, sadness, distress, calm, etc.
    distress_score = Column(Float, nullable=True)  # 0.0 to 100.0 (computed or standalone)
    engagement_score = Column(Float, nullable=False, default=1.0)  # 0.0 to 1.0
    
    raw_text = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship back to Victim
    victim = relationship("Victim", back_populates="check_ins")
