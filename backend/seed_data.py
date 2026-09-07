"""
Seed Database Script.

Populates the database with:
1. Standard demo users representing each role (district, state, national, counsellor)
2. Synthetic victim records under anonymized IDs (VIC-2024-*)
3. Longitudinal check-in sequences (Chatbot, IVRS, SMS)
4. Evaluated alerts for immediate dashboard demonstration

Default password for all demo accounts: 'password123'
"""

import sys
from datetime import datetime, timezone, timedelta
from database import SessionLocal, engine, Base
from models.user import User
from models.victim import Victim
from models.check_in import CheckIn
from models.alert import Alert
from services.auth import get_password_hash
import json


def seed_database():
    print("Initializing tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if users already exist
        if db.query(User).first():
            print("Database already contains data. Skipping seeding.")
            return {"status": "skipped", "message": "Database already contains data. Skipping seeding."}

        print("Seeding demo users...")
        hashed_pwd = get_password_hash("password123")

        users = [
            User(
                username="national_admin",
                email="national.admin@sih.gov.in",
                hashed_password=hashed_pwd,
                role="national",
                full_name="National Monitoring Officer",
                is_active=True,
            ),
            User(
                username="state_bihar",
                email="state.bihar@sih.gov.in",
                hashed_password=hashed_pwd,
                role="state",
                state="Bihar",
                full_name="Bihar State Protection Cell",
                is_active=True,
            ),
            User(
                username="district_patna",
                email="dm.patna@sih.gov.in",
                hashed_password=hashed_pwd,
                role="district",
                district="Patna",
                state="Bihar",
                full_name="Patna District Magistrate Cell",
                is_active=True,
            ),
            User(
                username="counsellor_priya",
                email="priya.counsellor@dmhp.org",
                hashed_password=hashed_pwd,
                role="counsellor",
                district="Patna",
                state="Bihar",
                full_name="Dr. Priya Sharma (DMHP Clinical Counsellor)",
                is_active=True,
            ),
            User(
                username="counsellor_anjali",
                email="anjali.counsellor@dmhp.org",
                hashed_password=hashed_pwd,
                role="counsellor",
                district="Patna",
                state="Bihar",
                full_name="Anjali Verma (District Counsellor)",
                is_active=True,
            ),
        ]
        db.add_all(users)
        db.commit()

        counsellor = db.query(User).filter(User.username == "counsellor_priya").first()

        print("Seeding synthetic victim cases...")
        now = datetime.now(timezone.utc)

        victims = [
            # 1. Critical deteriorating case (Key Demo Scenario)
            Victim(
                id="VIC-2024-00483",
                case_type="intimidation",
                registration_date=now - timedelta(days=25),
                assigned_district="Patna",
                assigned_state="Bihar",
                current_distress_score=78.5,
                current_trend="worsening",
                escalation_probability=0.92,
                risk_level="high",
                consent_flag=True,
                status="active",
                assigned_counsellor_id=counsellor.id,
            ),
            # 2. Stable low-risk case
            Victim(
                id="VIC-2024-00102",
                case_type="atrocity_act",
                registration_date=now - timedelta(days=40),
                assigned_district="Patna",
                assigned_state="Bihar",
                current_distress_score=24.0,
                current_trend="stable",
                escalation_probability=0.08,
                risk_level="low",
                consent_flag=True,
                status="active",
                assigned_counsellor_id=counsellor.id,
            ),
            # 3. Recovering case
            Victim(
                id="VIC-2024-00319",
                case_type="sexual_violence",
                registration_date=now - timedelta(days=60),
                assigned_district="Patna",
                assigned_state="Bihar",
                current_distress_score=35.0,
                current_trend="improving",
                escalation_probability=0.15,
                risk_level="low",
                consent_flag=True,
                status="monitoring",
                assigned_counsellor_id=counsellor.id,
            ),
            # 4. Another district case
            Victim(
                id="VIC-2024-00721",
                case_type="murder_threat",
                registration_date=now - timedelta(days=12),
                assigned_district="Gaya",
                assigned_state="Bihar",
                current_distress_score=68.0,
                current_trend="worsening",
                escalation_probability=0.74,
                risk_level="high",
                consent_flag=True,
                status="active",
            ),
            # 5. Uttar Pradesh case (for state filtering demo)
            Victim(
                id="VIC-2024-00905",
                case_type="atrocity_act",
                registration_date=now - timedelta(days=18),
                assigned_district="Lucknow",
                assigned_state="Uttar Pradesh",
                current_distress_score=42.0,
                current_trend="stable",
                escalation_probability=0.32,
                risk_level="moderate",
                consent_flag=True,
                status="active",
            ),
        ]
        db.add_all(victims)
        db.commit()

        print("Seeding longitudinal check-in trajectory...")
        # Check-ins for VIC-2024-00483 (Deteriorating victim journey)
        check_ins = [
            CheckIn(
                victim_id="VIC-2024-00483",
                channel="chatbot",
                timestamp=now - timedelta(days=18),
                sentiment_score=0.20,
                emotion_label="neutral",
                distress_score=30.0,
                engagement_score=1.0,
                raw_text="Court date is scheduled next month. Things are okay at home.",
            ),
            CheckIn(
                victim_id="VIC-2024-00483",
                channel="chatbot",
                timestamp=now - timedelta(days=12),
                sentiment_score=-0.25,
                emotion_label="anxiety",
                distress_score=48.0,
                engagement_score=0.85,
                raw_text="Some people from the accused's family were seen near our shop.",
            ),
            CheckIn(
                victim_id="VIC-2024-00483",
                channel="ivrs",
                timestamp=now - timedelta(days=6),
                sentiment_score=-0.65,
                emotion_label="fear",
                distress_score=68.0,
                engagement_score=0.60,
                raw_text="They came to my house last night and threatened my brother. We cannot sleep.",
            ),
            CheckIn(
                victim_id="VIC-2024-00483",
                channel="chatbot",
                timestamp=now - timedelta(hours=14),
                sentiment_score=-0.85,
                emotion_label="distress",
                distress_score=82.0,
                engagement_score=0.45,
                raw_text="I am terrified. We want to withdraw the complaint, please help us.",
            ),
            # Check-ins for VIC-2024-00102 (Stable case)
            CheckIn(
                victim_id="VIC-2024-00102",
                channel="chatbot",
                timestamp=now - timedelta(days=15),
                sentiment_score=0.40,
                emotion_label="calm",
                distress_score=25.0,
                engagement_score=1.0,
                raw_text="The police patrol visited yesterday. Everything is peaceful.",
            ),
            CheckIn(
                victim_id="VIC-2024-00102",
                channel="sms",
                timestamp=now - timedelta(days=2),
                sentiment_score=0.35,
                emotion_label="hope",
                distress_score=22.0,
                engagement_score=1.0,
                raw_text="Received compensation interim relief. Thank you for your support.",
            ),
        ]
        db.add_all(check_ins)
        db.commit()

        print("Seeding active alert for demo...")
        alert = Alert(
            victim_id="VIC-2024-00483",
            triggered_at=now - timedelta(hours=14),
            risk_level="critical",
            status="open",
            assigned_to=counsellor.id,
            distress_score=82.0,
            escalation_probability=0.92,
            trigger_reason="Distress score (82.0) crossed threshold (70.0); Escalation probability (92%) crossed safety limit (60%)",
            explanation_factors=json.dumps([
                {
                    "factor": "Declining sentiment trend",
                    "contribution": 22.5,
                    "description": "Sentiment dropped sharply from +0.20 to -0.85 across the last 4 check-ins"
                },
                {
                    "factor": "High threat & fear signals",
                    "contribution": 20.0,
                    "description": "Predominant emotions shifted to fear and acute distress following witness intimidation"
                },
                {
                    "factor": "Engagement decline",
                    "contribution": 8.5,
                    "description": "Response brevity and delayed check-ins indicating withdrawal"
                }
            ]),
            recommended_actions=json.dumps([
                {
                    "category": "protection",
                    "title": "Immediate Threat Assessment & Police Escort",
                    "description": "Dispatch local Special Cell to assess perimeter security and escort victim.",
                    "priority": "immediate",
                    "recommended_authority": "District Superintendent of Police / Witness Protection Cell"
                },
                {
                    "category": "counselling",
                    "title": "Crisis Trauma De-escalation Call",
                    "description": "Conduct emergency trauma session within 24 hours.",
                    "priority": "immediate",
                    "recommended_authority": "Assigned Case Counsellor"
                }
            ]),
        )
        db.add(alert)
        db.commit()

        print("\nSeed completed successfully!")
        print("Demo Accounts Created (Password: 'password123'):")
        print("  - National:   national_admin")
        print("  - State:      state_bihar")
        print("  - District:   district_patna")
        print("  - Counsellor: counsellor_priya")

        return {"status": "success", "message": "Demo accounts and synthetic cases seeded successfully."}
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
