"""
ML Pipeline Client.

Communicates via HTTP with the ML Pipeline service (default: http://localhost:8001).
Invokes:
  - POST /score/distress
  - POST /explain/distress
  - POST /predict/escalation
  - POST /analyze/text
"""

import logging
from typing import Dict, List, Optional
import httpx

from config import ML_PIPELINE_URL

logger = logging.getLogger(__name__)


class MLPipelineClient:
    def __init__(self, base_url: str = ML_PIPELINE_URL):
        self.base_url = base_url.rstrip("/")

    async def score_distress(self, victim_id: str, interactions: List[Dict]) -> Dict:
        """Call POST /score/distress on ML pipeline."""
        url = f"{self.base_url}/score/distress"
        payload = {
            "victim_id": victim_id,
            "interactions": interactions,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Error calling ML pipeline /score/distress: %s", e)
                # Fallback calculation if ML pipeline temporarily unavailable
                return self._fallback_distress_score(victim_id, interactions)

    async def explain_distress(self, victim_id: str, interactions: List[Dict]) -> Dict:
        """Call POST /explain/distress on ML pipeline."""
        url = f"{self.base_url}/explain/distress"
        payload = {
            "victim_id": victim_id,
            "interactions": interactions,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Error calling ML pipeline /explain/distress: %s", e)
                return self._fallback_distress_score(victim_id, interactions)

    async def predict_escalation(self, victim_id: str, history: List[Dict], window_days: int = 7) -> Dict:
        """Call POST /predict/escalation on ML pipeline."""
        url = f"{self.base_url}/predict/escalation"
        payload = {
            "victim_id": victim_id,
            "history": history,
            "prediction_window_days": window_days,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Error calling ML pipeline /predict/escalation: %s", e)
                return self._fallback_escalation_prediction(victim_id, history)

    async def analyze_text(self, text: str, language: str = "en") -> Dict:
        """Call POST /analyze/text on ML pipeline."""
        url = f"{self.base_url}/analyze/text"
        payload = {"text": text, "language": language}
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Error calling ML pipeline /analyze/text: %s", e)
                return {
                    "sentiment": {"label": "neutral", "confidence": 0.5},
                    "emotions": [{"label": "neutral", "score": 0.5}],
                }

    def _fallback_distress_score(self, victim_id: str, interactions: List[Dict]) -> Dict:
        """Heuristic fallback calculation if ML pipeline service is offline."""
        if not interactions:
            return {"victim_id": victim_id, "distress_score": 0.0, "trend": "stable", "confidence": 0.0, "factors": []}
        
        last = interactions[-1]
        sent = last.get("sentiment_score", 0.0)
        distress_score = round(max(0.0, min(100.0, (1.0 - (sent + 1.0) / 2.0) * 100.0)), 1)
        return {
            "victim_id": victim_id,
            "distress_score": distress_score,
            "trend": "stable",
            "trend_detail": "Computed via fallback heuristic (ML service offline)",
            "confidence": 0.5,
            "factors": [
                {
                    "factor": "Recent sentiment polarity",
                    "contribution": distress_score,
                    "description": f"Sentiment {sent:+.2f} indicates distress level: +{distress_score:.0f} pts"
                }
            ],
            "interactions_analyzed": len(interactions),
        }

    def _fallback_escalation_prediction(self, victim_id: str, history: List[Dict]) -> Dict:
        """Heuristic fallback calculation for escalation probability."""
        if not history:
            return {"victim_id": victim_id, "escalation_probability": 0.1, "risk_level": "low", "escalation_likely": False}
        last_score = history[-1].get("distress_score", 0.0)
        prob = round(min(0.99, max(0.01, last_score / 100.0)), 2)
        return {
            "victim_id": victim_id,
            "escalation_probability": prob,
            "risk_level": "high" if prob >= 0.65 else "moderate" if prob >= 0.35 else "low",
            "escalation_likely": prob >= 0.50,
            "predicted_trend": "stable",
            "summary": "Computed via fallback heuristic (ML service offline)",
            "key_signals": [],
            "data_points_analyzed": len(history),
        }


ml_client = MLPipelineClient()
