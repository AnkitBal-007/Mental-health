"""Pydantic models for Recommended Interventions."""

from typing import List, Optional, Any
from pydantic import BaseModel, Field


class InterventionItem(BaseModel):
    category: str = Field(
        ...,
        description="counselling, medical, protection, relocation, financial, legal_aid"
    )
    title: str = Field(..., description="Actionable intervention title")
    description: str = Field(..., description="Clear operational guidance for counsellor or official")
    priority: str = Field(..., description="immediate, high, medium, routine")
    recommended_authority: str = Field(..., description="e.g., District Legal Services Authority (DLSA), Special Cell, CMO")
    ranking_score: float = Field(..., description="Computed priority score for ranking interventions")
    reason: str = Field(..., description="Transparent justification for why this intervention was triggered")


class VictimRecommendationsResponse(BaseModel):
    victim_id: str
    case_type: str
    risk_level: str
    current_distress_score: float
    escalation_probability: float
    contributing_factors_evaluated: List[str] = Field(
        default_factory=list,
        description="Psychological and situational factors used in evaluating recommendations"
    )
    total_recommendations: int
    interventions: List[InterventionItem]
    rules_config_source: str = Field(
        default="config/recommendation_rules.json",
        description="Path or provenance of the editable rules configuration"
    )

