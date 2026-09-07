"""Pydantic models for POST /score/distress."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class InteractionRecord(BaseModel):
    """
    A single check-in interaction to feed into distress scoring.

    The backend assembles these from stored check-in data before calling
    the scoring endpoint.
    """

    sentiment_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Sentiment polarity: -1 (very negative) to +1 (very positive)",
    )
    emotion_label: str = Field(
        ..., description="Primary emotion detected (e.g. fear, sadness, calm)"
    )
    engagement_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Engagement level: 1.0 = fully engaged, 0.0 = missed/disengaged",
    )
    timestamp: datetime = Field(..., description="When this check-in occurred")
    check_in_type: str = Field(
        default="chatbot",
        description="Channel used: chatbot, ivrs, or sms",
    )


class DistressScoreRequest(BaseModel):
    """Request body for the distress scoring endpoint."""

    victim_id: str = Field(
        ..., description="Anonymized/pseudonymized victim identifier"
    )
    interactions: List[InteractionRecord] = Field(
        ...,
        min_length=1,
        description="Recent interaction records, ordered by timestamp",
    )


class DistressFactor(BaseModel):
    """
    One contributing factor to the distress score.

    Shown in the dashboard's explainability panel as a plain-language
    statement with its point contribution. Per design guidelines, factors
    are ordered by contribution size (largest first).
    """

    factor: str = Field(..., description="Human-readable factor name")
    contribution: float = Field(
        ..., description="Approximate point contribution to the 0-100 score"
    )
    detail: str = Field(
        ..., description="Plain-language explanation of this factor"
    )


class DistressScoreResponse(BaseModel):
    """Response from the distress scoring endpoint."""

    victim_id: str
    distress_score: float = Field(..., ge=0, le=100)
    trend: str = Field(..., description="improving, stable, or worsening")
    trend_detail: str = Field(..., description="Plain-language trend explanation")
    confidence: float = Field(
        ..., ge=0, le=1, description="Confidence in the score — increases with more data"
    )
    factors: List[DistressFactor] = Field(
        ..., description="Contributing factors, ordered by contribution (largest first)"
    )
    interactions_analyzed: int
    computed_at: datetime


# ---------------------------------------------------------------------------
# POST /explain/distress — detailed explainability breakdown
# ---------------------------------------------------------------------------


class ExplainFactor(BaseModel):
    """
    A single explainability factor for the distress score.

    Designed so the frontend can render it directly as:
      "Declining sentiment trend: +18 points"
      "Missed last 2 check-ins: +12 points"

    Uses SHAP values when a trained model is involved; otherwise uses
    transparent rule-based weighted contributions.
    """

    factor: str = Field(
        ..., description="Short human-readable factor name"
    )
    contribution: float = Field(
        ..., description="Point contribution to the 0-100 distress score"
    )
    description: str = Field(
        ...,
        description="Plain-language explanation suitable for non-technical reviewers",
    )


class ExplainDistressResponse(BaseModel):
    """Response from the explainability endpoint."""

    victim_id: str
    distress_score: float = Field(..., ge=0, le=100)
    trend: str = Field(..., description="improving, stable, or worsening")
    trend_detail: str = Field(..., description="Plain-language trend explanation")
    scoring_method: str = Field(
        ...,
        description="'rule-based' or 'model-based (SHAP)' — indicates how factors were derived",
    )
    factors: List[ExplainFactor] = Field(
        ...,
        description="Contributing factors, ordered by contribution (largest first). "
        "Contributions sum approximately to the distress score.",
    )
    confidence: float = Field(
        ..., ge=0, le=1, description="Confidence in the score"
    )
    interactions_analyzed: int
    computed_at: datetime
