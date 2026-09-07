"""Router for POST /score/distress."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from schemas.distress import DistressScoreRequest, DistressScoreResponse
from services.distress_scorer import compute_distress_score, compute_trend

router = APIRouter(prefix="/score", tags=["Distress Scoring"])


@router.post("/distress", response_model=DistressScoreResponse)
async def score_distress(request: DistressScoreRequest):
    """
    Compute a Dynamic Distress Score (0-100) from recent interaction records.

    Returns the score, trend direction (improving / stable / worsening),
    contributing factors in plain language (ordered by contribution, largest
    first), and a confidence value that increases with more data points.

    The scoring formula is rule-based for the prototype; see
    services/distress_scorer.py for the full breakdown and swap instructions.
    """
    try:
        # Compute distress score with factor breakdown
        score_result = compute_distress_score(request.interactions)

        # Compute trend direction
        trend_label, trend_detail = compute_trend(request.interactions)

        return DistressScoreResponse(
            victim_id=request.victim_id,
            distress_score=score_result["distress_score"],
            trend=trend_label,
            trend_detail=trend_detail,
            confidence=score_result["confidence"],
            factors=score_result["factors"],
            interactions_analyzed=score_result["interactions_analyzed"],
            computed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {e}")
