"""
Alert Evaluation Service.

Coordinates evaluation of victim check-ins, communicates with the ML Pipeline,
triggers alerts when distress or escalation thresholds are breached, and
generates explainable intervention packages.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session

from config import DISTRESS_ALERT_THRESHOLD, ESCALATION_PROB_THRESHOLD
from models.victim import Victim
from models.check_in import CheckIn
from models.alert import Alert
from models.audit_log import AuditLog
from schemas.alert import AlertEvaluationResult, AlertResponse
from services.ml_client import ml_client
from services.recommendations import get_recommendations_for_victim

logger = logging.getLogger(__name__)


async def evaluate_victim_alerts(
    db: Session,
    victim_id: str,
    custom_distress_threshold: Optional[float] = None,
    custom_escalation_threshold: Optional[float] = None,
    evaluator_username: Optional[str] = "system",
) -> AlertEvaluationResult:
    """
    Evaluate victim check-ins through the ML Pipeline and trigger alerts if needed.
    """
    victim = db.query(Victim).filter(Victim.id == victim_id).first()
    if not victim:
        raise ValueError(f"Victim with ID '{victim_id}' not found")

    distress_threshold = custom_distress_threshold or DISTRESS_ALERT_THRESHOLD
    escalation_threshold = custom_escalation_threshold or ESCALATION_PROB_THRESHOLD

    # Fetch chronological check-ins for the victim
    check_ins = (
        db.query(CheckIn)
        .filter(CheckIn.victim_id == victim_id)
        .order_by(CheckIn.timestamp.asc())
        .all()
    )

    # Format interaction records for ML Pipeline
    interactions = []
    score_history = []
    
    for ci in check_ins:
        ci_dict = {
            "sentiment_score": ci.sentiment_score,
            "emotion_label": ci.emotion_label,
            "engagement_score": ci.engagement_score,
            "timestamp": ci.timestamp.isoformat(),
            "check_in_type": ci.channel,
        }
        interactions.append(ci_dict)
        
        score_val = ci.distress_score if ci.distress_score is not None else 50.0
        score_history.append({
            "distress_score": score_val,
            "timestamp": ci.timestamp.isoformat(),
        })

    # Call ML Pipeline: Explain Distress & Predict Escalation
    if interactions:
        distress_data = await ml_client.explain_distress(victim_id, interactions)
    else:
        distress_data = {
            "distress_score": victim.current_distress_score or 0.0,
            "trend": victim.current_trend or "stable",
            "factors": [],
        }

    computed_score = float(distress_data.get("distress_score", 0.0))
    trend_val = str(distress_data.get("trend", "stable"))
    factors = distress_data.get("factors", [])

    # Update score history with latest computed score
    if not score_history:
        score_history.append({
            "distress_score": computed_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    else:
        score_history[-1]["distress_score"] = computed_score

    # Call escalation prediction model
    escalation_data = await ml_client.predict_escalation(victim_id, score_history)
    escalation_prob = float(escalation_data.get("escalation_probability", 0.0))
    risk_level = str(escalation_data.get("risk_level", "low"))

    # Update victim cached metrics
    victim.current_distress_score = computed_score
    victim.current_trend = trend_val
    victim.escalation_probability = escalation_prob
    victim.risk_level = risk_level
    victim.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Determine if alert condition is met
    score_breach = computed_score >= distress_threshold
    escalation_breach = escalation_prob >= escalation_threshold

    alert_created = False
    created_alert_obj: Optional[Alert] = None
    recommended_items = get_recommendations_for_victim(
        case_type=victim.case_type,
        risk_level=risk_level if (score_breach or escalation_breach) else "low",
        distress_score=computed_score,
        escalation_prob=escalation_prob,
    )

    if score_breach or escalation_breach:
        # Avoid spamming duplicate open alerts for the same victim within the last 12 hours
        twelve_hours_ago = datetime.now(timezone.utc) - timedelta(hours=12)
        existing_alert = (
            db.query(Alert)
            .filter(
                Alert.victim_id == victim_id,
                Alert.status.in_(["open", "assigned", "under_review"]),
                Alert.triggered_at >= twelve_hours_ago,
            )
            .first()
        )

        reasons = []
        if score_breach:
            reasons.append(f"Distress score ({computed_score:.1f}) crossed threshold ({distress_threshold:.1f})")
        if escalation_breach:
            reasons.append(f"Escalation probability ({escalation_prob:.0%}) crossed safety limit ({escalation_threshold:.0%})")
        trigger_reason = "; ".join(reasons)

        alert_risk = "critical" if (computed_score >= 85.0 or escalation_prob >= 0.85) else "high"

        if not existing_alert:
            new_alert = Alert(
                victim_id=victim_id,
                triggered_at=datetime.now(timezone.utc),
                risk_level=alert_risk,
                status="open",
                assigned_to=victim.assigned_counsellor_id,
                distress_score=computed_score,
                escalation_probability=escalation_prob,
                trigger_reason=trigger_reason,
                explanation_factors=json.dumps(factors),
                recommended_actions=json.dumps([r.model_dump() for r in recommended_items]),
            )
            db.add(new_alert)
            db.commit()
            db.refresh(new_alert)
            created_alert_obj = new_alert
            alert_created = True

            # Write to audit log
            audit = AuditLog(
                action="ALERT_TRIGGERED",
                target_victim_id=victim_id,
                username=evaluator_username,
                details=f"Created {alert_risk} alert: {trigger_reason}",
            )
            db.add(audit)
            db.commit()
        else:
            created_alert_obj = existing_alert

    alert_resp = None
    if created_alert_obj:
        exp_factors = created_alert_obj.explanation_factors
        if isinstance(exp_factors, str):
            try:
                exp_factors = json.loads(exp_factors)
            except Exception:
                pass

        rec_actions = created_alert_obj.recommended_actions
        if isinstance(rec_actions, str):
            try:
                rec_actions = json.loads(rec_actions)
            except Exception:
                pass

        alert_resp = AlertResponse(
            id=created_alert_obj.id,
            victim_id=created_alert_obj.victim_id,
            triggered_at=created_alert_obj.triggered_at,
            risk_level=created_alert_obj.risk_level,
            status=created_alert_obj.status,
            assigned_to=created_alert_obj.assigned_to,
            distress_score=created_alert_obj.distress_score,
            escalation_probability=created_alert_obj.escalation_probability,
            trigger_reason=created_alert_obj.trigger_reason,
            explanation_factors=exp_factors,
            recommended_actions=rec_actions,
            resolution_notes=created_alert_obj.resolution_notes,
            resolved_at=created_alert_obj.resolved_at,
            created_at=created_alert_obj.created_at,
        )

    return AlertEvaluationResult(
        victim_id=victim_id,
        alert_created=alert_created,
        distress_score=computed_score,
        trend=trend_val,
        escalation_probability=escalation_prob,
        risk_level=risk_level,
        alert=alert_resp,
        explanation=factors,
        recommended_interventions=[r.model_dump() for r in recommended_items],
        evaluated_at=datetime.now(timezone.utc),
    )
