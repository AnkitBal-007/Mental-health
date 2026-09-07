"""Router for Dashboard Summary and Jurisdictional Aggregations."""

import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.victim import Victim
from models.alert import Alert
from models.user import User
from schemas.dashboard import DashboardSummaryResponse
from schemas.alert import AlertResponse
from services.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _format_alert_response(alert: Alert) -> AlertResponse:
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


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    scope: str = Query("national", description="district, state, or national"),
    id: Optional[str] = Query(None, description="District or State name (e.g. 'Patna' or 'Bihar')"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve aggregated dashboard statistics filtered by administrative scope.
    
    Role Enforcement:
      - District users can only view their own district.
      - State users can only view their state or districts within their state.
      - National users have nationwide aggregate and drill-down access.
    """
    scope_clean = scope.lower()
    if scope_clean not in ["district", "state", "national"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid scope. Must be 'district', 'state', or 'national'.",
        )

    # Validate role authority vs requested scope
    if current_user.role == "district":
        if scope_clean != "district" or (id and id != current_user.district):
            scope_clean = "district"
            id = current_user.district
    elif current_user.role == "state":
        if scope_clean == "national":
            scope_clean = "state"
            id = current_user.state

    # Base queries
    victim_query = db.query(Victim)
    alert_query = db.query(Alert).join(Victim, Alert.victim_id == Victim.id)

    # Apply scope filters
    if scope_clean == "district" and id:
        victim_query = victim_query.filter(Victim.assigned_district == id)
        alert_query = alert_query.filter(Victim.assigned_district == id)
    elif scope_clean == "state" and id:
        victim_query = victim_query.filter(Victim.assigned_state == id)
        alert_query = alert_query.filter(Victim.assigned_state == id)

    # 1. Monitored victims count
    total_victims = victim_query.count()

    # 2. Active alerts (open, assigned, under_review)
    active_alerts_count = alert_query.filter(Alert.status.in_(["open", "assigned", "under_review"])).count()

    # 3. Alerts this week
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    alerts_this_week = alert_query.filter(Alert.triggered_at >= one_week_ago).count()

    # 4. Average distress score
    avg_score_res = victim_query.with_entities(func.avg(Victim.current_distress_score)).scalar()
    avg_distress_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0

    # 5. Risk category counts
    high_risk_count = victim_query.filter(Victim.risk_level == "high").count()
    moderate_risk_count = victim_query.filter(Victim.risk_level == "moderate").count()
    low_risk_count = victim_query.filter(Victim.risk_level.in_(["low", None])).count()

    # 6. Trend distribution
    trend_counts = {"improving": 0, "stable": 0, "worsening": 0}
    trends_raw = (
        victim_query.with_entities(Victim.current_trend, func.count(Victim.id))
        .group_by(Victim.current_trend)
        .all()
    )
    for trend_name, count in trends_raw:
        if trend_name in trend_counts:
            trend_counts[trend_name] = count
        elif trend_name:
            trend_counts[trend_name.lower()] = count

    # 7. Case type distribution
    case_type_counts = {}
    case_types_raw = (
        victim_query.with_entities(Victim.case_type, func.count(Victim.id))
        .group_by(Victim.case_type)
        .all()
    )
    for ctype, count in case_types_raw:
        if ctype:
            case_type_counts[ctype] = count

    # 8. Recent active alerts
    recent_alerts_raw = (
        alert_query.filter(Alert.status.in_(["open", "assigned", "under_review"]))
        .order_by(Alert.triggered_at.desc())
        .limit(5)
        .all()
    )
    recent_alerts = [_format_alert_response(a) for a in recent_alerts_raw]

    return DashboardSummaryResponse(
        scope=scope_clean,
        scope_id=id or "all",
        total_monitored_victims=total_victims,
        active_alerts=active_alerts_count,
        alerts_this_week=alerts_this_week,
        average_distress_score=avg_distress_score,
        high_risk_cases=high_risk_count,
        moderate_risk_cases=moderate_risk_count,
        low_risk_cases=low_risk_count,
        trend_distribution=trend_counts,
        case_type_distribution=case_type_counts,
        recent_alerts=recent_alerts,
    )
