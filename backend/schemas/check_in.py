"""Pydantic models for Check-ins."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CheckInCreate(BaseModel):
    victim_id: str = Field(..., description="Target victim anonymized ID")
    channel: str = Field(default="chatbot", description="chatbot, ivrs, sms, portal")
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0, description="Sentiment polarity (-1 to 1)")
    emotion_label: str = Field(default="neutral", description="fear, sadness, distress, calm, etc.")
    distress_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Standalone check-in distress score if known")
    engagement_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Engagement level (0 to 1)")
    raw_text: Optional[str] = Field(default=None, description="Raw text from user response if available")
    text_content: Optional[str] = Field(default=None, description="Alias for raw text from frontend")
    timestamp: Optional[datetime] = None


class CheckInResponse(BaseModel):
    id: int
    victim_id: str
    channel: str
    timestamp: datetime
    sentiment_score: float
    emotion_label: str
    distress_score: Optional[float] = None
    engagement_score: float
    raw_text: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CheckInListResponse(BaseModel):
    total: int
    items: List[CheckInResponse]
