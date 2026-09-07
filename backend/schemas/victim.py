"""Pydantic models for Victims."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class VictimCreate(BaseModel):
    id: str = Field(..., description="Anonymized ID, e.g. VIC-2024-001")
    case_type: str = Field(..., description="e.g. atrocity_act, intimidation, sexual_violence, grievous_hurt")
    assigned_district: str = Field(..., description="District jurisdiction, e.g. Patna")
    assigned_state: str = Field(..., description="State jurisdiction, e.g. Bihar")
    consent_flag: Optional[bool] = Field(default=True, description="Victim consent for proactive monitoring")
    assigned_counsellor_id: Optional[int] = None


class VictimUpdate(BaseModel):
    case_type: Optional[str] = None
    assigned_district: Optional[str] = None
    assigned_state: Optional[str] = None
    assigned_counsellor_id: Optional[int] = None
    status: Optional[str] = None
    consent_flag: Optional[bool] = None


class VictimResponse(BaseModel):
    id: str
    case_type: str
    registration_date: datetime
    assigned_district: str
    assigned_state: str
    current_distress_score: float
    current_trend: str
    escalation_probability: float
    risk_level: str
    consent_flag: bool
    status: str
    assigned_counsellor_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VictimListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[VictimResponse]
