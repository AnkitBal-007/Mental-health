"""Router for POST /analyze/text."""

from fastapi import APIRouter, HTTPException

from schemas.text import TextAnalysisRequest, TextAnalysisResponse
from services.text_analyzer import text_analyzer

router = APIRouter(prefix="/analyze", tags=["Text Analysis"])


@router.post("/text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze text for sentiment and emotion.

    Supports Hindi and English (and other languages covered by the
    underlying XLM-RoBERTa model).  Returns sentiment classification
    (positive / neutral / negative with confidence) and emotion scores
    across the configured emotion labels.
    """
    if not text_analyzer.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Text analysis models are still loading. Try again shortly.",
        )

    try:
        result = text_analyzer.analyze(request.text, request.language)
        return TextAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
