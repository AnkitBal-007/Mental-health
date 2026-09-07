"""Pydantic models for POST /predict/escalation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ScoreRecord(BaseModel):
    """A single historical distress score entry for a victim."""

    distress_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Distress score value (0 to 100)",
        examples=[45.0],
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp when the score was computed/recorded",
        examples=["2024-12-01T10:00:00Z"],
    )


class EscalationPredictionRequest(BaseModel):
    """Request body for distress escalation prediction."""

    victim_id: str = Field(
        ...,
        description="Anonymized/pseudonymized victim identifier",
        examples=["VIC-2024-00483"],
    )
    history: List[ScoreRecord] = Field(
        ...,
        min_length=1,
        description="Time series of past distress scores with timestamps, ordered chronologically",
    )
    prediction_window_days: Optional[int] = Field(
        default=7,
        ge=1,
        le=30,
        description="Forecast horizon in days (default: 7 days / next check-in window)",
    )


class FeatureImportanceItem(BaseModel):
    """Feature contribution or importance factor for the escalation prediction."""

    feature: str = Field(..., description="Feature name")
    value: float = Field(..., description="Observed value in the victim's history")
    impact: str = Field(..., description="Plain-language description of how this affects risk")


class EscalationPredictionResponse(BaseModel):
    """Response payload with escalation probability and explanation."""

    victim_id: str
    escalation_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated probability (0-1) of significant distress escalation before next check-in",
    )
    risk_level: str = Field(
        ...,
        description="'low' (prob < 0.35), 'moderate' (0.35 - 0.65), or 'high' (prob > 0.65)",
    )
    escalation_likely: bool = Field(
        ...,
        description="Binary flag (True if probability >= 0.50 threshold)",
    )
    predicted_trend: str = Field(
        ...,
        description="Short summary: 'sharp_increase', 'gradual_increase', 'stable', or 'improving'",
    )
    summary: str = Field(
        ...,
        description="Plain-language explanation of prediction for officials/counsellors",
    )
    key_signals: List[FeatureImportanceItem] = Field(
        default_factory=list,
        description="Key trajectory signals extracted from the historical time series",
    )
    data_points_analyzed: int
    model_provenance: str = Field(
        default="Synthetic longitudinal dataset (Scikit-Learn Gradient Boosting Classifier)",
        description="Provenance of the model per project rules",
    )
    computed_at: datetime
