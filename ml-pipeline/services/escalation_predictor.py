"""
Escalation Prediction Service.

Predicts the probability that a victim's psychological distress will significantly
escalate before the next check-in window (e.g. within 7 days).

MODEL ARCHITECTURE:
- Scikit-Learn GradientBoostingClassifier trained on synthetic longitudinal data.
- Transparent feature extraction capturing velocity, volatility, acceleration,
  and recent shifts in distress scores.

COMPLIANCE & PROVENANCE:
- 100% Synthetic training data generated via synthetic_trajectory_generator.py.
- Model is lightweight, auditable, and returns key signals for full explainability.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

from schemas.escalation import ScoreRecord, FeatureImportanceItem
from services.synthetic_trajectory_generator import (
    FEATURE_NAMES,
    extract_features_from_scores,
    generate_synthetic_dataset,
)

logger = logging.getLogger(__name__)


class EscalationPredictor:
    """Gradient-boosted escalation prediction service."""

    def __init__(self) -> None:
        self.model: GradientBoostingClassifier = None
        self._is_trained: bool = False

    def train_model(self, n_samples: int = 4000) -> None:
        """
        Train the gradient boosting classifier on synthetic trajectory data.

        Executed on application startup.
        """
        logger.info("Generating synthetic trajectory dataset for escalation prediction (%d samples)...", n_samples)
        X, y = generate_synthetic_dataset(n_samples=n_samples, random_seed=42)

        logger.info("Training GradientBoostingClassifier for distress escalation prediction...")
        self.model = GradientBoostingClassifier(
            n_estimators=60,
            learning_rate=0.1,
            max_depth=3,
            random_state=42,
        )
        self.model.fit(X, y)
        self._is_trained = True

        train_acc = self.model.score(X, y)
        logger.info("Escalation predictor trained successfully. Synthetic training accuracy: %.2f%%", train_acc * 100)

    @property
    def is_loaded(self) -> bool:
        return self._is_trained

    def predict(self, victim_id: str, history: List[ScoreRecord], window_days: int = 7) -> Dict:
        """
        Predict escalation risk given historical distress scores.
        """
        if not self._is_trained:
            logger.warning("Model was not trained yet. Training now...")
            self.train_model()

        # Sort history chronologically
        sorted_history = sorted(history, key=lambda x: x.timestamp)
        scores = [r.distress_score for r in sorted_history]
        n_points = len(scores)

        # Extract features
        features = extract_features_from_scores(scores)
        feat_2d = features.reshape(1, -1)

        # Model probability: P(escalation = 1)
        prob_escalation = float(self.model.predict_proba(feat_2d)[0][1])

        # If single point, use a baseline heuristic calibrated to the current score
        if n_points == 1:
            curr = scores[0]
            prob_escalation = round(min(0.95, max(0.05, curr / 100.0 * 0.8)), 4)

        # Assign risk level
        if prob_escalation >= 0.65:
            risk_level = "high"
            likely = True
        elif prob_escalation >= 0.35:
            risk_level = "moderate"
            likely = prob_escalation >= 0.50
        else:
            risk_level = "low"
            likely = False

        # Determine predicted trend label
        latest_score = features[0]
        velocity = features[3]  # slope
        recent_delta = features[4]

        if velocity > 3.0 or recent_delta >= 10.0:
            predicted_trend = "sharp_increase"
        elif velocity > 0.5 or recent_delta >= 4.0:
            predicted_trend = "gradual_increase"
        elif velocity < -1.0 or recent_delta <= -5.0:
            predicted_trend = "improving"
        else:
            predicted_trend = "stable"

        # Construct key signals list with plain-language explanations
        signals: List[FeatureImportanceItem] = []

        signals.append(
            FeatureImportanceItem(
                feature="Current Distress Level",
                value=round(latest_score, 1),
                impact=(
                    f"Latest recorded score is {latest_score:.1f}/100 "
                    f"({'critically high' if latest_score >= 70 else 'elevated' if latest_score >= 45 else 'manageable'})."
                ),
            )
        )

        if n_points >= 2:
            signals.append(
                FeatureImportanceItem(
                    feature="Recent Trajectory Velocity",
                    value=round(velocity, 2),
                    impact=(
                        f"Distress is trending {'upward (+%.1f pts/check-in)' % velocity if velocity > 0 else 'downward (%.1f pts/check-in)' % velocity if velocity < 0 else 'flat'}."
                    ),
                )
            )
            signals.append(
                FeatureImportanceItem(
                    feature="Last Check-in Shift",
                    value=round(recent_delta, 1),
                    impact=(
                        f"Score shifted by {recent_delta:+.1f} points between the last two interactions."
                    ),
                )
            )

        if n_points >= 3 and features[2] > 5.0:
            signals.append(
                FeatureImportanceItem(
                    feature="Score Volatility",
                    value=round(features[2], 2),
                    impact=f"High score variability (std: {features[2]:.1f}) indicates emotional instability or situational triggers.",
                )
            )

        # Plain language summary
        if risk_level == "high":
            summary = (
                f"High risk of acute distress escalation (probability: {prob_escalation:.0%}) "
                f"within the next {window_days} days. Trajectory shows {predicted_trend.replace('_', ' ')} "
                f"with current score at {latest_score:.0f}. Early counsellor outreach recommended."
            )
        elif risk_level == "moderate":
            summary = (
                f"Moderate probability ({prob_escalation:.0%}) of distress escalation before the next check-in. "
                f"Distress trend is {predicted_trend.replace('_', ' ')}. Continued routine monitoring advised."
            )
        else:
            summary = (
                f"Low risk of escalation ({prob_escalation:.0%}). Victim's distress trajectory appears "
                f"{predicted_trend.replace('_', ' ')} with manageable distress indicators."
            )

        return {
            "victim_id": victim_id,
            "escalation_probability": round(prob_escalation, 4),
            "risk_level": risk_level,
            "escalation_likely": likely,
            "predicted_trend": predicted_trend,
            "summary": summary,
            "key_signals": signals,
            "data_points_analyzed": n_points,
            "model_provenance": "Synthetic longitudinal dataset (Scikit-Learn Gradient Boosting Classifier)",
            "computed_at": datetime.now(timezone.utc),
        }


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------
escalation_predictor = EscalationPredictor()
