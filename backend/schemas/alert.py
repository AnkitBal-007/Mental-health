"""Pydantic models for Alerts and Alert Evaluation."""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class AlertEvaluateRequest(BaseModel):
    victim_id: str = Field(..., description="Target victim ID to evaluate across recent check-ins")
    custom_distress_threshold: Optional[float] = Field(default=None, ge=0, le=100)
    custom_escalation_threshold: Optional[float] = Field(default=None, ge=0, le=1)


class AlertUpdate(BaseModel):
    status: Optional[str] = Field(None, description="open, assigned, under_review, resolved, dismissed")
    assigned_to: Optional[int] = Field(None, description="User ID of assignee")
    resolution_notes: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    victim_id: str
    triggered_at: datetime
    risk_level: str
    status: str
    assigned_to: Optional[int] = None
    distress_score: float
    escalation_probability: float
    trigger_reason: str
    explanation_factors: Optional[Any] = None
    recommended_actions: Optional[Any] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    total: int
    items: List[AlertResponse]


class AlertEvaluationResult(BaseModel):
    victim_id: str
    alert_created: bool
    distress_score: float
    trend: str
    escalation_probability: float
    risk_level: str
    alert: Optional[AlertResponse] = None
    explanation: Optional[Any] = None
    recommended_interventions: Optional[List[Any]] = None
    evaluated_at: datetime
