"""Router for Alerts and ML-Driven Alert Evaluation."""

import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.alert import Alert
from models.victim import Victim
from models.user import User
from models.audit_log import AuditLog
from schemas.alert import (
    AlertEvaluateRequest,
    AlertEvaluationResult,
    AlertResponse,
    AlertListResponse,
    AlertUpdate,
)
from services.auth import get_current_user
from services.alert_evaluator import evaluate_victim_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _format_alert_response(alert: Alert) -> AlertResponse:
    """Helper to deserialize JSON text fields into objects."""
    exp_factors = alert.explanation_factors
    if isinstance(exp_factors, str):
        try:
            exp_factors = json.loads(exp_factors)
        except Exception:
            pass

    rec_actions = alert.recommended_actions
    if isinstance(rec_actions, str):
        try:
            rec_actions = json.loads(rec_actions)
        except Exception:
            pass

    return AlertResponse(
        id=alert.id,
        victim_id=alert.victim_id,
        triggered_at=alert.triggered_at,
        risk_level=alert.risk_level,
        status=alert.status,
        assigned_to=alert.assigned_to,
        distress_score=alert.distress_score,
        escalation_probability=alert.escalation_probability,
        trigger_reason=alert.trigger_reason,
        explanation_factors=exp_factors,
        recommended_actions=rec_actions,
        resolution_notes=alert.resolution_notes,
        resolved_at=alert.resolved_at,
        created_at=alert.created_at,
    )


@router.post("/evaluate", response_model=AlertEvaluationResult)
async def evaluate_alert_for_victim(
    request: AlertEvaluateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Evaluate a victim's recent check-in trajectory through the ML Pipeline.
    
    1. Fetches historical check-ins for the victim.
    2. Calls ML pipeline `/score/distress` (or `/explain/distress`) and `/predict/escalation`.
    3. If distress score >= 70 or predicted escalation prob >= 0.60:
       Creates an Alert record with plain-language explanations and recommended actions.
    4. Updates cached victim risk metrics in the database.
    """
    try:
        result = await evaluate_victim_alerts(
            db=db,
            victim_id=request.victim_id,
            custom_distress_threshold=request.custom_distress_threshold,
            custom_escalation_threshold=request.custom_escalation_threshold,
            evaluator_username=current_user.username,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {e}",
        )


@router.get("", response_model=AlertListResponse)
def list_alerts(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    victim_id: Optional[str] = None,
    assigned_to: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List alerts prioritized by severity and recency."""
    query = db.query(Alert).join(Victim, Alert.victim_id == Victim.id)

    # Apply role jurisdiction filter
    if current_user.role == "district" and current_user.district:
        query = query.filter(Victim.assigned_district == current_user.district)
    elif current_user.role == "state" and current_user.state:
        query = query.filter(Victim.assigned_state == current_user.state)
    elif current_user.role == "counsellor":
        if current_user.district:
            query = query.filter(
                (Victim.assigned_district == current_user.district) |
                (Alert.assigned_to == current_user.id)
            )
        else:
            query = query.filter(Alert.assigned_to == current_user.id)

    if status and status != "all":
        query = query.filter(Alert.status == status)
    if risk_level:
        query = query.filter(Alert.risk_level == risk_level.lower())
    if victim_id:
        query = query.filter(Alert.victim_id == victim_id)
    if assigned_to:
        query = query.filter(Alert.assigned_to == assigned_to)

    total = query.count()
    raw_items = (
        query.order_by(Alert.triggered_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_format_alert_response(a) for a in raw_items]
    return AlertListResponse(total=total, items=items)


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single alert details."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert #{alert_id} not found",
        )
    return _format_alert_response(alert)


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign alert to a counsellor or update resolution status."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert #{alert_id} not found",
        )

    if alert_update.status:
        alert.status = alert_update.status
        if alert_update.status in ["resolved", "dismissed"]:
            alert.resolved_at = datetime.now(timezone.utc)

    if alert_update.assigned_to is not None:
        alert.assigned_to = alert_update.assigned_to

    if alert_update.resolution_notes:
        alert.resolution_notes = alert_update.resolution_notes

    db.commit()
    db.refresh(alert)

    # Write audit log
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        action="UPDATE_ALERT",
        target_victim_id=alert.victim_id,
        details=f"Updated alert #{alert.id} status to '{alert.status}', assigned to User ID {alert.assigned_to}",
    )
    db.add(audit)
    db.commit()

    return _format_alert_response(alert)
