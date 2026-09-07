"""Pydantic models for POST /analyze/voice."""

from pydantic import BaseModel, Field
from typing import Optional


class ProsodicFeatures(BaseModel):
    """Acoustic features extracted from the audio signal."""

    pitch_mean_hz: float = Field(
        ..., description="Mean fundamental frequency in Hz"
    )
    pitch_variance: float = Field(
        ..., description="Variance of pitch — elevated values may indicate stress"
    )
    speaking_rate_syllables_per_sec: float = Field(
        ..., description="Estimated syllables per second (onset-based)"
    )
    pause_ratio: float = Field(
        ..., ge=0, le=1, description="Ratio of silence to total duration"
    )
    energy_mean: float = Field(..., description="Mean RMS energy of the signal")
    energy_variance: float = Field(
        ..., description="Variance of RMS energy — irregularity may indicate distress"
    )


class StressIndicators(BaseModel):
    """Rule-based stress flags derived from prosodic features."""

    pitch_elevated: bool = Field(
        ..., description="True if pitch variance exceeds stress threshold"
    )
    speech_rate_abnormal: bool = Field(
        ..., description="True if speaking rate is unusually fast or slow"
    )
    high_pause_ratio: bool = Field(
        ..., description="True if pause ratio exceeds 0.4 (long silences)"
    )
    energy_irregular: bool = Field(
        ..., description="True if energy variance is abnormally high"
    )
    overall_stress_level: str = Field(
        ..., description="Aggregated level: low, moderate, or high"
    )


class VoiceAnalysisResponse(BaseModel):
    """Response from voice analysis endpoint."""

    transcript: str
    language_detected: Optional[str] = None
    duration_seconds: float
    prosodic_features: ProsodicFeatures
    stress_indicators: StressIndicators
