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
    
    If raw text is provided without sentiment scores, the backend calls the
    ML pipeline /analyze/text endpoint to extract sentiment and emotion in real time.
    """
    victim = db.query(Victim).filter(Victim.id == check_in_in.victim_id).first()
    if not victim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Victim with ID '{check_in_in.victim_id}' does not exist",
        )

    # Check consent flag (opt-out honored at data collection layer)
    if not victim.consent_flag:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Victim has opted out of monitoring data collection",
        )

    sentiment = check_in_in.sentiment_score
    emotion = check_in_in.emotion_label

    # If raw text is provided and no explicit sentiment set, query ML pipeline
    if check_in_in.raw_text and sentiment == 0.0 and emotion == "neutral":
        nlp_res = await ml_client.analyze_text(check_in_in.raw_text)
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
        victim_id=check_in_in.victim_id,
        channel=check_in_in.channel,
        timestamp=check_in_in.timestamp or datetime.now(timezone.utc),
        sentiment_score=sentiment,
        emotion_label=emotion,
        distress_score=check_in_in.distress_score,
        engagement_score=check_in_in.engagement_score,
        raw_text=check_in_in.raw_text,
    )
    db.add(check_in)
    db.commit()
    db.refresh(check_in)

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
