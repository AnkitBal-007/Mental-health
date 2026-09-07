"""Router for POST /predict/escalation."""

from fastapi import APIRouter, HTTPException

from schemas.escalation import EscalationPredictionRequest, EscalationPredictionResponse
from services.escalation_predictor import escalation_predictor

router = APIRouter(prefix="/predict", tags=["Escalation Prediction"])


@router.post("/escalation", response_model=EscalationPredictionResponse)
async def predict_escalation(request: EscalationPredictionRequest):
    """
    Predict probability of significant distress escalation before the next check-in.

    Accepts a time-series history of distress scores with timestamps for one victim.
    Extracts trajectory features (velocity, recent delta, volatility, acceleration)
    and estimates the probability using a Scikit-Learn Gradient Boosting Classifier
    trained on synthetic longitudinal trajectory patterns.

    **Provenance Note:**
    Trained on 100% synthetic longitudinal data with realistic patterns (gradual decline,
    sudden trigger spike, recovering trend, stable low-risk) for prototype purposes.
    """
    try:
        result = escalation_predictor.predict(
            victim_id=request.victim_id,
            history=request.history,
            window_days=request.prediction_window_days or 7,
        )
        return EscalationPredictionResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Escalation prediction failed: {e}"
        )
