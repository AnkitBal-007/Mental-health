"""Router for POST /explain/distress."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from schemas.distress import DistressScoreRequest, ExplainDistressResponse
from services.distress_scorer import explain_distress_score

router = APIRouter(prefix="/explain", tags=["Explainability"])


@router.post("/distress", response_model=ExplainDistressResponse)
async def explain_distress(request: DistressScoreRequest):
    """
    Explain a distress score with a ranked, human-readable factor breakdown.

    Returns the same distress score as /score/distress, plus a detailed list
    of {factor, contribution, description} objects ordered by contribution
    (largest first).  Factor contributions sum approximately to the total
    distress score.

    Current implementation uses a transparent rule-based weighted breakdown.
    When a trained model (XGBoost / scikit-learn) is used, this endpoint
    will switch to SHAP-based explanations automatically.

    Factors include:
      - Current sentiment level
      - Declining sentiment trend
      - Negative emotion predominance
      - High emotional volatility
      - Latest check-in severity
      - Missed check-ins
      - Engagement decline
    """
    try:
        result = explain_distress_score(request.interactions)

        return ExplainDistressResponse(
            victim_id=request.victim_id,
            distress_score=result["distress_score"],
            trend=result["trend"],
            trend_detail=result["trend_detail"],
            scoring_method=result["scoring_method"],
            factors=result["factors"],
            confidence=result["confidence"],
            interactions_analyzed=result["interactions_analyzed"],
            computed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Explanation failed: {e}"
        )
