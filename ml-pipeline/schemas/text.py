"""Pydantic models for POST /analyze/text."""

from pydantic import BaseModel, Field
from typing import List


class TextAnalysisRequest(BaseModel):
    """Request body for text sentiment and emotion analysis."""

    text: str = Field(
        ...,
        min_length=1,
        description="Text to analyze (chatbot message, transcribed IVRS, etc.)",
        examples=["I feel very scared and alone after the hearing."],
    )
    language: str = Field(
        default="en",
        description="Language code — 'en' for English, 'hi' for Hindi",
        examples=["en", "hi"],
    )


class SentimentResult(BaseModel):
    """Top-level sentiment classification."""

    label: str = Field(..., description="positive, neutral, or negative")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence 0-1")


class EmotionScore(BaseModel):
    """Single emotion with its classification score."""

    label: str = Field(..., description="Emotion label (e.g. fear, sadness, calm)")
    score: float = Field(..., ge=0, le=1, description="Classification score 0-1")


class TextAnalysisResponse(BaseModel):
    """Response from text analysis endpoint."""

    sentiment: SentimentResult
    emotions: List[EmotionScore]
    language: str
    text_length: int
