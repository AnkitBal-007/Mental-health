"""Router for Check-in operations across all channels."""

from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.check_in import CheckIn
from models.victim import Victim
from models.user import User
from schemas.check_in import CheckInCreate, CheckInResponse, CheckInListResponse
from services.auth import get_current_user, get_optional_current_user
from services.ml_client import ml_client

router = APIRouter(prefix="/check-ins", tags=["Check-ins"])


@router.get("", response_model=CheckInListResponse)
def list_all_check_ins(
    victim_id: Optional[str] = None,
    channel: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List check-in interactions across channels."""
    query = db.query(CheckIn)
    if victim_id:
        query = query.filter(CheckIn.victim_id == victim_id)
    if channel:
        query = query.filter(CheckIn.channel == channel)

    total = query.count()
    items = (
        query.order_by(CheckIn.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return CheckInListResponse(total=total, items=items)


@router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_check_in(
    check_in_in: CheckInCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Record a new check-in from Chatbot, IVRS, SMS, or Portal.
    
    If victim ID is not found, it is automatically registered as a guest/active case
    so all chatbot interactions appear seamlessly on the backend dashboard.
    """
    raw_v_id = (check_in_in.victim_id or "").strip().upper()
    if not raw_v_id or raw_v_id in ["GUEST", "ANONYMOUS", "PUBLIC", "DEFAULT"]:
        raw_v_id = "VIC-2024-GUEST"

    victim = db.query(Victim).filter(Victim.id == raw_v_id).first()
    if not victim:
        # Automatically register incoming chatbot / new case
        init_score = check_in_in.distress_score if check_in_in.distress_score is not None else 50.0
        init_risk = "high" if init_score >= 70 else ("moderate" if init_score >= 40 else "low")
        victim = Victim(
            id=raw_v_id,
            case_type="intimidation" if init_score >= 65 else "counselling_support",
            assigned_district="Patna",
            assigned_state="Bihar",
            consent_flag=True,
            current_distress_score=round(float(init_score), 1),
            risk_level=init_risk,
            current_trend="stable",
            status="active",
        )
        db.add(victim)
        db.commit()
        db.refresh(victim)

    # Check consent flag (opt-out honored at data collection layer)
    if not victim.consent_flag:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Victim has opted out of monitoring data collection",
        )

    text_to_analyze = check_in_in.raw_text or check_in_in.text_content
    sentiment = check_in_in.sentiment_score
    emotion = check_in_in.emotion_label

    # If raw text is provided and no explicit sentiment set, query ML pipeline
    if text_to_analyze and sentiment == 0.0 and emotion == "neutral":
        nlp_res = await ml_client.analyze_text(text_to_analyze)
        sent_info = nlp_res.get("sentiment", {})
        sent_label = sent_info.get("label", "neutral")
        sent_conf = sent_info.get("confidence", 0.5)

        if sent_label == "positive":
            sentiment = round(sent_conf * 0.8, 2)
        elif sent_label == "negative":
            sentiment = round(-sent_conf * 0.8, 2)
        else:
            sentiment = 0.0

        emotions = nlp_res.get("emotions", [])
        if emotions:
            emotion = emotions[0].get("label", "neutral")

    check_in = CheckIn(
        victim_id=victim.id,
        channel=check_in_in.channel or "chatbot",
        timestamp=check_in_in.timestamp or datetime.now(timezone.utc),
        sentiment_score=sentiment,
        emotion_label=emotion,
        distress_score=check_in_in.distress_score,
        engagement_score=check_in_in.engagement_score,
        raw_text=text_to_analyze,
    )
    db.add(check_in)

    # Update victim metrics immediately on dashboard
    if check_in_in.distress_score is not None:
        new_score = round(float(check_in_in.distress_score), 1)
        old_score = float(victim.current_distress_score or 50.0)
        victim.current_distress_score = new_score
        if new_score >= 80:
            victim.risk_level = "critical"
        elif new_score >= 65:
            victim.risk_level = "high"
        elif new_score >= 40:
            victim.risk_level = "moderate"
        else:
            victim.risk_level = "low"

        if new_score > old_score + 5:
            victim.current_trend = "worsening"
        elif new_score < old_score - 5:
            victim.current_trend = "improving"
        else:
            victim.current_trend = "stable"

    victim.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(check_in)

    # Trigger ML alert evaluation if distress or risk indicators are elevated
    if (check_in_in.distress_score and check_in_in.distress_score >= 65) or emotion in ["fear", "distress", "sadness", "anger"] or sentiment <= -0.3:
        try:
            from services.alert_evaluator import evaluate_victim_alerts
            await evaluate_victim_alerts(db=db, victim_id=victim.id, evaluator_username="saheli_chatbot")
        except Exception:
            pass

    return check_in


@router.get("/{check_in_id}", response_model=CheckInResponse)
def get_check_in(
    check_in_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details of an individual check-in record."""
    check_in = db.query(CheckIn).filter(CheckIn.id == check_in_id).first()
    if not check_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Check-in #{check_in_id} not found",
        )
    return check_in
