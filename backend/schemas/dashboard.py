"""Pydantic models for Dashboard Aggregations."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from schemas.alert import AlertResponse


class DashboardSummaryResponse(BaseModel):
    scope: str = Field(..., description="district, state, or national")
    scope_id: Optional[str] = Field(None, description="Identifier for district/state, or 'all'")
    
    total_monitored_victims: int
    active_alerts: int
    alerts_this_week: int
    
    average_distress_score: float
    high_risk_cases: int
    moderate_risk_cases: int
    low_risk_cases: int
    
    trend_distribution: Dict[str, int] = Field(
        ...,
        description="Count of cases by trend: improving, stable, worsening"
    )
    case_type_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of cases by case type"
    )
    recent_alerts: List[AlertResponse] = Field(
        default_factory=list,
        description="Latest high-priority active alerts within scope"
    )
