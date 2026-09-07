"""Router for Victim management and jurisdictional queries."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.victim import Victim
from models.check_in import CheckIn
from models.user import User
from models.audit_log import AuditLog
from schemas.victim import VictimCreate, VictimUpdate, VictimResponse, VictimListResponse
from schemas.check_in import CheckInResponse
from schemas.recommendation import VictimRecommendationsResponse
from services.auth import get_current_user
from services.recommendations import get_recommendations_for_victim, evaluate_recommendations

router = APIRouter(prefix="/victims", tags=["Victims"])


def apply_jurisdiction_filter(query, user: User):
    """
    Enforces server-side jurisdictional role scoping per design rules:
    - District users: see only their assigned district's victims.
    - State users: see only their assigned state's victims.
    - National users: see all records nationwide.
    - Counsellor: see victims in their district or directly assigned to them.
    """
    if user.role == "district" and user.district:
        return query.filter(Victim.assigned_district == user.district)
    elif user.role == "state" and user.state:
        return query.filter(Victim.assigned_state == user.state)
    elif user.role == "counsellor":
        if user.district:
            return query.filter(
                (Victim.assigned_district == user.district) | 
                (Victim.assigned_counsellor_id == user.id)
            )
        return query.filter(Victim.assigned_counsellor_id == user.id)
    return query


@router.get("", response_model=VictimListResponse)
def list_victims(
    district: Optional[str] = None,
    state: Optional[str] = None,
    risk_level: Optional[str] = None,
    case_type: Optional[str] = None,
    status: Optional[str] = "active",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List monitored victims with filtering and sorting by risk level.
    Enforces server-side role scoping.
    """
    query = db.query(Victim)
    query = apply_jurisdiction_filter(query, current_user)

    if district:
        query = query.filter(Victim.assigned_district == district)
    if state:
        query = query.filter(Victim.assigned_state == state)
    if risk_level:
        query = query.filter(Victim.risk_level == risk_level.lower())
    if case_type:
        query = query.filter(Victim.case_type == case_type)
    if status and status != "all":
        query = query.filter(Victim.status == status)

    total = query.count()
    items = (
        query.order_by(Victim.current_distress_score.desc(), Victim.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return VictimListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.post("", response_model=VictimResponse, status_code=status.HTTP_201_CREATED)
def create_victim(
    victim_in: VictimCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new victim case under an anonymized identifier."""
    existing = db.query(Victim).filter(Victim.id == victim_in.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Victim with ID '{victim_in.id}' already exists",
        )

    victim = Victim(
        id=victim_in.id,
        case_type=victim_in.case_type,
        assigned_district=victim_in.assigned_district,
        assigned_state=victim_in.assigned_state,
        consent_flag=victim_in.consent_flag if victim_in.consent_flag is not None else True,
        assigned_counsellor_id=victim_in.assigned_counsellor_id,
        current_distress_score=0.0,
        current_trend="stable",
        risk_level="low",
        status="active",
    )
    db.add(victim)
    db.commit()
    db.refresh(victim)

    # Audit log entry
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        action="REGISTER_VICTIM",
        target_victim_id=victim.id,
        details=f"Registered case type: {victim.case_type} in {victim.assigned_district}, {victim.assigned_state}",
    )
    db.add(audit)
    db.commit()

    return victim


@router.get("/{victim_id}", response_model=VictimResponse)
def get_victim_detail(
    victim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific victim case."""
    query = db.query(Victim).filter(Victim.id == victim_id)
    query = apply_jurisdiction_filter(query, current_user)
    victim = query.first()

    if not victim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Victim with ID '{victim_id}' not found or outside authorized jurisdiction",
        )

    # Audit log of viewing sensitive victim profile
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        action="VIEW_VICTIM_DETAIL",
        target_victim_id=victim.id,
        details=f"Viewed case profile",
    )
    db.add(audit)
    db.commit()

    return victim


@router.put("/{victim_id}", response_model=VictimResponse)
def update_victim(
    victim_id: str,
    victim_update: VictimUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update victim attributes, assigned counsellor, or case status."""
    query = db.query(Victim).filter(Victim.id == victim_id)
    query = apply_jurisdiction_filter(query, current_user)
    victim = query.first()

    if not victim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Victim with ID '{victim_id}' not found or outside authorized jurisdiction",
        )

    update_data = victim_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(victim, field, value)

    db.commit()
    db.refresh(victim)
    return victim


@router.get("/{victim_id}/check-ins", response_model=List[CheckInResponse])
def get_victim_check_ins(
    victim_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List historical check-ins for a victim."""
    query = db.query(Victim).filter(Victim.id == victim_id)
    query = apply_jurisdiction_filter(query, current_user)
    victim = query.first()

    if not victim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Victim '{victim_id}' not found or outside authorized jurisdiction",
        )

    check_ins = (
        db.query(CheckIn)
        .filter(CheckIn.victim_id == victim_id)
        .order_by(CheckIn.timestamp.desc())
        .limit(limit)
        .all()
    )
    return check_ins


@router.get("/{victim_id}/recommendations", response_model=VictimRecommendationsResponse)
def get_victim_recommendations(
    victim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve evidence-backed, ranked suggested interventions based on the victim's
    current distress score, contributing factors, and legal case type.
    
    Rules are loaded dynamically from config/recommendation_rules.json so they
    can be customized and inspected during evaluation without restarting the server.
    """
    query = db.query(Victim).filter(Victim.id == victim_id)
    query = apply_jurisdiction_filter(query, current_user)
    victim = query.first()

    if not victim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Victim '{victim_id}' not found or outside authorized jurisdiction",
        )

    # Extract psychological & situational factors from recent check-ins
    factors_extracted = []
    recent_check_ins = (
        db.query(CheckIn)
        .filter(CheckIn.victim_id == victim_id)
        .order_by(CheckIn.timestamp.desc())
        .limit(5)
        .all()
    )
    for ci in recent_check_ins:
        if ci.emotion_label:
            factors_extracted.append(ci.emotion_label)
        if ci.sentiment_score < -0.3:
            factors_extracted.append("declining sentiment")
            factors_extracted.append("negative mood")
        if ci.engagement_score < 0.5:
            factors_extracted.append("low engagement")

    if victim.current_distress_score >= 65:
        factors_extracted.append("high distress")
        factors_extracted.append("severe anxiety")

    # Evaluate rules from JSON configuration
    interventions = evaluate_recommendations(
        case_type=victim.case_type,
        distress_score=victim.current_distress_score or 0.0,
        contributing_factors=factors_extracted,
        escalation_prob=victim.escalation_probability or 0.0,
    )

    return VictimRecommendationsResponse(
        victim_id=victim.id,
        case_type=victim.case_type,
        risk_level=victim.risk_level or "low",
        current_distress_score=victim.current_distress_score or 0.0,
        escalation_probability=victim.escalation_probability or 0.0,
        contributing_factors_evaluated=list(set(factors_extracted)),
        total_recommendations=len(interventions),
        interventions=interventions,
        rules_config_source="config/recommendation_rules.json",
    )

