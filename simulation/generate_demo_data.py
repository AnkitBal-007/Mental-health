#!/usr/bin/env python3
"""
=============================================================================
MindGuard — Synthetic Demo Data Generator
=============================================================================

Generates realistic longitudinal check-in data for 6 demo victims across
4 distinct distress trajectories, then seeds them into the backend via its
REST API. Running this script populates the dashboard with a believable
multi-week dataset ready for a live demonstration.

TRAJECTORIES MODELLED
─────────────────────
  1. Gradual Decline      — Starts moderate, deteriorates over 6–8 weeks
  2. Sudden Trigger       — Stable until a court date triggers sharp drop
  3. Stable Low-Risk      — Consistently low distress, wellness maintained
  4. Recovery             — Starts high, gradually improves with support

VICTIMS CREATED (all in District: Patna, State: Bihar)
────────────────────────────────────────────────────────
  VIC-2024-10001  Sunita Devi       atrocity_act         Recovery
  VIC-2024-10002  Priya Sharma      sexual_violence      Gradual Decline ⚠ alert
  VIC-2024-10003  Kavita Rani       intimidation         Sudden Trigger  ⚠ alert
  VIC-2024-10004  Radha Singh       murder_witness       Stable Low-Risk
  VIC-2024-10005  Meena Devi        caste_based_violence Gradual Decline (moderate)
  VIC-2024-10006  Poonam Kumari     grievous_hurt        Recovery

USAGE
─────
  cd "c:\\Users\\Ankit007\\OneDrive\\Documents\\SIH project 1\\simulation"
  py generate_demo_data.py

  Options:
    --backend   Backend base URL   (default: http://localhost:8000)
    --username  Login username     (default: district_patna)
    --password  Login password     (default: password123)
    --dry-run   Print payloads without calling the API
    --reset     Delete & recreate victims (skip if already exists)

NOTE: This script uses SYNTHETIC data only. No real victim information.
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

import requests

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ─── Configuration ────────────────────────────────────────────────────────────

BACKEND_URL = "http://localhost:8000"
ML_URL      = "http://localhost:8001"

# ─── Response text pools (realistic multilingual check-in messages) ───────────

RESPONSES = {
    # severity 1–2: very positive / stable
    "very_positive": [
        "I am feeling much better today. The counsellor's advice really helped.",
        "आज मैं ठीक हूँ। परिवार के साथ अच्छा समय बिताया।",
        "Things are improving. I slept well last night and feel hopeful.",
        "The legal aid session went well today. I feel supported.",
        "मुझे लग रहा है सब ठीक हो जाएगा। थोड़ा हल्का महसूस हो रहा है।",
        "I went for a walk with my sister today. It felt good to be outside.",
    ],
    # severity 3–4: okay / slightly low
    "mild_positive": [
        "I am managing. Not great, but not bad either.",
        "आज ठीक-ठाक रहा। नींद थोड़ी कम थी लेकिन खाना खाया।",
        "Some difficult moments but overall I am okay today.",
        "I have been keeping myself busy with household work.",
        "थोड़ी थकान है। लेकिन आज काम किया और मन हल्का हुआ।",
        "The counsellor called today. It was helpful to talk.",
    ],
    # severity 5–6: neutral / mild struggle
    "neutral": [
        "I don't know how to explain it. Some days are harder than others.",
        "मुझे थोड़ी बेचैनी है। ठीक से नहीं पता क्या करूँ।",
        "Sleep is not good. I keep thinking about what happened.",
        "I feel tired most of the time. But I am trying.",
        "आज ज़्यादा बात नहीं करना चाहती। बस ठीक हूँ।",
        "Worrying about the court date. I hope it goes well.",
        "Feeling unsettled. Not sure about the future.",
    ],
    # severity 7–8: distressed
    "distressed": [
        "I have not been sleeping well. I feel very anxious and worried all the time.",
        "मुझे बहुत डर लग रहा है। रात को नींद नहीं आती।",
        "Everything feels hopeless. I don't know how long I can go on like this.",
        "मन बहुत भारी है। किसी से मिलने का मन नहीं करता।",
        "I feel like nobody understands what I am going through. I feel very alone.",
        "I am scared to leave the house. My appetite is gone.",
        "बहुत गुस्सा और दुख है। कोई नहीं समझता।",
    ],
    # severity 9–10: severe / crisis
    "severe": [
        "I am in a very bad state today. I cannot eat or sleep. I am terrified.",
        "मुझे धमकी मिली है। मैं बहुत डरी हुई हूँ। कृपया मदद करें।",
        "Someone called me and threatened me. I don't feel safe at all.",
        "मैं यहाँ सुरक्षित नहीं हूँ। मुझे बहुत डर लग रहा है।",
        "I feel completely hopeless and trapped. I cannot take this anymore.",
        "बहुत बुरा हो रहा है। मैं अकेली हूँ और बहुत डरी हुई हूँ।",
        "The accused party is threatening my family. I am in severe distress.",
    ],
    # trigger event specific
    "trigger_event": [
        "The court date happened today. They were there and stared at me the whole time. I feel sick.",
        "आज कोर्ट में उनसे सामना हुआ। मैं बहुत घबरा गई। रोती रही।",
        "Someone from the other side called and warned me to withdraw the case. I am terrified.",
        "मुझे धमकी मिली कि मैं गवाही नहीं दूँगी तो परिणाम भुगतूंगी।",
        "They followed me on my way back from court today. I am shaking.",
    ],
    # recovery messages
    "recovering": [
        "The counselling session was very helpful. I am starting to feel a little better.",
        "मेरे काउंसलर ने बहुत मदद की। अब थोड़ा ठीक लग रहा है।",
        "I slept a little better last night. Things are slowly improving.",
        "The legal aid officer was kind and explained everything to me.",
        "मुझे लग रहा है मुझे सही मदद मिल रही है। आज बेहतर हूँ।",
        "I feel much better than I did two weeks ago. Thank you for checking in.",
    ],
}

CHANNELS = ["chatbot", "ivrs", "sms", "portal"]

# ─── Trajectory definitions ────────────────────────────────────────────────────
# Each turn = { severity (1-10), channel_weights, response_pool }
# Severity maps → sentiment_score, emotion_label, distress_score

def severity_to_features(severity: float, noise: float = 0.5):
    """Convert a severity (1–10) to sentiment_score, emotion_label, distress_score."""
    s = max(1.0, min(10.0, severity + random.uniform(-noise, noise)))

    # distress_score: severity 1 → ~10, severity 10 → ~95
    distress = 8 + (s - 1) * 9.5 + random.uniform(-3, 3)
    distress = max(5.0, min(98.0, distress))

    # sentiment_score: -1 (very negative) to +1 (positive)
    sentiment = 1.0 - (s / 5.0)
    sentiment = max(-1.0, min(1.0, sentiment + random.uniform(-0.15, 0.15)))

    # emotion based on severity range
    if s <= 2.5:
        emotion = random.choice(["calm", "relief", "hopeful"])
    elif s <= 4.5:
        emotion = random.choice(["calm", "neutral", "mild_anxiety"])
    elif s <= 6.5:
        emotion = random.choice(["anxiety", "sadness", "neutral", "worry"])
    elif s <= 8.0:
        emotion = random.choice(["distress", "fear", "sadness", "anger"])
    else:
        emotion = random.choice(["severe_distress", "terror", "hopelessness", "fear"])

    # engagement drops as distress rises
    engagement = max(0.1, 1.0 - (s / 12.0) + random.uniform(-0.1, 0.1))

    return {
        "sentiment_score": round(sentiment, 4),
        "emotion_label": emotion,
        "distress_score": round(distress, 1),
        "engagement_score": round(engagement, 3),
    }


def pick_response(severity: float) -> str:
    if severity <= 2.5:
        return random.choice(RESPONSES["very_positive"])
    elif severity <= 4.0:
        return random.choice(RESPONSES["mild_positive"])
    elif severity <= 5.5:
        return random.choice(RESPONSES["neutral"])
    elif severity <= 7.5:
        return random.choice(RESPONSES["distressed"])
    else:
        return random.choice(RESPONSES["severe"])


def pick_channel(turn_index: int, pattern: str) -> str:
    """Return a channel with realistic distribution."""
    weights = {
        "chatbot": 0.45,
        "sms":     0.30,
        "ivrs":    0.20,
        "portal":  0.05,
    }
    return random.choices(list(weights.keys()), list(weights.values()))[0]


# ─── Generate trajectory: list of severity values ────────────────────────────

def gradual_decline_trajectory(n: int, start: float = 3.5, end: float = 8.5) -> list:
    """Gradually worsening — scores climb from start to end."""
    return [round(start + (end - start) * (i / (n - 1)), 2) for i in range(n)]


def sudden_trigger_trajectory(n: int, trigger_at: int = 7) -> list:
    """Stable until trigger_at turn, then sharp drop."""
    scores = []
    for i in range(n):
        if i < trigger_at:
            scores.append(round(random.uniform(2.5, 4.0), 2))
        elif i == trigger_at:
            scores.append(round(random.uniform(8.5, 10.0), 2))  # trigger spike
        else:
            # Stays elevated after trigger
            scores.append(round(random.uniform(7.0, 9.0), 2))
    return scores


def stable_low_trajectory(n: int) -> list:
    """Consistently low distress throughout."""
    return [round(random.uniform(1.5, 3.5), 2) for _ in range(n)]


def recovery_trajectory(n: int, start: float = 8.0, end: float = 2.5) -> list:
    """High distress at start, steadily improving."""
    return [round(start + (end - start) * (i / (n - 1)), 2) for i in range(n)]


def moderate_decline_trajectory(n: int) -> list:
    """Gradual decline but stays in moderate range (doesn't trigger alert)."""
    return [round(random.uniform(3.0 + (i * 0.3), 5.5 + (i * 0.2)), 2) for i in range(n)]


# ─── Victim configurations ────────────────────────────────────────────────────

VICTIMS = [
    {
        "id": "VIC-2024-10001",
        "case_type": "atrocity_act",
        "assigned_district": "Patna",
        "assigned_state": "Bihar",
        "consent_flag": True,
        "trajectory": "recovery",
        "n_checkins": 12,
        "description": "Sunita Devi — SC/ST Atrocities Act case, starting in crisis, responding well to interventions.",
        "evaluate_alert_at": None,  # No alert expected
        "assigned_counsellor_id": 4,
    },
    {
        "id": "VIC-2024-10002",
        "case_type": "sexual_violence",
        "assigned_district": "Patna",
        "assigned_state": "Bihar",
        "consent_flag": True,
        "trajectory": "gradual_decline",
        "n_checkins": 14,
        "description": "Priya Sharma — Sexual violence case, emotionally deteriorating, ALERT should trigger at turn 9.",
        "evaluate_alert_at": 9,  # ← alert will be triggered here
        "assigned_counsellor_id": 4,
    },
    {
        "id": "VIC-2024-10003",
        "case_type": "intimidation",
        "assigned_district": "Patna",
        "assigned_state": "Bihar",
        "consent_flag": True,
        "trajectory": "sudden_trigger",
        "n_checkins": 11,
        "description": "Kavita Rani — Witness intimidation case, stable until a threatening phone call triggers acute distress.",
        "evaluate_alert_at": 8,  # ← alert triggered after the spike
        "trigger_at": 6,         # 0-indexed turn where trigger happens
        "assigned_counsellor_id": 4,
    },
    {
        "id": "VIC-2024-10004",
        "case_type": "murder_witness",
        "assigned_district": "Patna",
        "assigned_state": "Bihar",
        "consent_flag": True,
        "trajectory": "stable_low",
        "n_checkins": 10,
        "description": "Radha Singh — Murder witness, consistently low distress, strong family support.",
        "evaluate_alert_at": None,
        "assigned_counsellor_id": 4,
    },
    {
        "id": "VIC-2024-10005",
        "case_type": "caste_based_violence",
        "assigned_district": "Patna",
        "assigned_state": "Bihar",
        "consent_flag": True,
        "trajectory": "moderate_decline",
        "n_checkins": 13,
        "description": "Meena Devi — Caste-based violence, gradual moderate decline, needs monitoring.",
        "evaluate_alert_at": None,
        "assigned_counsellor_id": 4,
    },
    {
        "id": "VIC-2024-10006",
        "case_type": "grievous_hurt",
        "assigned_district": "Patna",
        "assigned_state": "Bihar",
        "consent_flag": True,
        "trajectory": "recovery",
        "n_checkins": 12,
        "description": "Poonam Kumari — Grievous hurt case, initially very distressed, recovering with legal aid support.",
        "evaluate_alert_at": None,
        "assigned_counsellor_id": 4,
    },
]


# ─── API Client ────────────────────────────────────────────────────────────────

class BackendClient:
    def __init__(self, base_url: str, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def login(self, username: str, password: str) -> bool:
        print(f"\n🔐 Authenticating as '{username}'…")
        if self.dry_run:
            print("   [DRY RUN] Skipping login.")
            self.token = "dry_run_token"
            return True
        try:
            res = self.session.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            res.raise_for_status()
            self.token = res.json()["access_token"]
            self.session.headers["Authorization"] = f"Bearer {self.token}"
            print("   ✅ Authenticated.")
            return True
        except Exception as e:
            print(f"   ❌ Login failed: {e}")
            return False

    def create_victim(self, payload: dict) -> Optional[dict]:
        victim_id = payload["id"]
        if self.dry_run:
            print(f"   [DRY RUN] Would POST /victims: {victim_id}")
            return {"id": victim_id}
        try:
            res = self.session.post(f"{self.base_url}/victims", json=payload, timeout=10)
            if res.status_code == 409 or "already exists" in res.text.lower():
                print(f"   ℹ  Victim {victim_id} already exists — skipping creation.")
                return {"id": victim_id}
            res.raise_for_status()
            return res.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in (400, 409, 422):
                print(f"   ℹ  Victim {victim_id} may already exist ({e.response.status_code}) — continuing.")
                return {"id": victim_id}
            print(f"   ❌ Failed to create victim {victim_id}: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Error creating victim {victim_id}: {e}")
            return None

    def create_check_in(self, payload: dict) -> Optional[dict]:
        if self.dry_run:
            vid = payload.get("victim_id")
            ds = payload.get("distress_score")
            em = payload.get("emotion_label")
            print(f"      [DRY RUN] Would POST /check-ins: {vid} | score={ds} | {em}")
            return {"distress_score": ds}
        try:
            res = self.session.post(f"{self.base_url}/check-ins", json=payload, timeout=15)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"      ⚠  Check-in failed: {e}")
            return None

    def evaluate_alert(self, victim_id: str) -> Optional[dict]:
        if self.dry_run:
            print(f"   [DRY RUN] Would POST /alerts/evaluate for {victim_id}")
            return {}
        try:
            res = self.session.post(
                f"{self.base_url}/alerts/evaluate",
                json={"victim_id": victim_id},
                timeout=30,  # Calls ML pipeline — needs longer timeout
            )
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"   ⚠  Alert evaluation failed: {e}")
            return None


# ─── Main seeding logic ────────────────────────────────────────────────────────

def generate_timestamps(n: int, span_days: int = 60) -> list:
    """
    Generate n timestamps spread across span_days (≈ 2 months),
    working backwards from now. Not perfectly uniform — adds realistic gaps.
    """
    now = datetime.utcnow()
    start = now - timedelta(days=span_days)

    # Generate n random timestamps in ascending order
    offsets = sorted(random.uniform(0, span_days * 24 * 3600) for _ in range(n))
    return [start + timedelta(seconds=o) for o in offsets]


def build_checkin_payload(victim_id: str, turn_index: int, n_turns: int,
                          trajectory_name: str, severity: float,
                          timestamp: datetime, trigger_at: Optional[int] = None) -> dict:
    """Build a single check-in payload for the API."""
    features = severity_to_features(severity)

    # Choose response text
    if (trigger_at is not None and turn_index == trigger_at):
        text = random.choice(RESPONSES["trigger_event"])
    elif trajectory_name == "recovery" and turn_index >= n_turns // 2:
        text = random.choice(RESPONSES["recovering"])
    else:
        text = pick_response(severity)

    channel = pick_channel(turn_index, trajectory_name)

    return {
        "victim_id": victim_id,
        "channel": channel,
        "raw_text": text,
        "sentiment_score": features["sentiment_score"],
        "emotion_label": features["emotion_label"],
        "distress_score": features["distress_score"],
        "engagement_score": features["engagement_score"],
        "timestamp": timestamp.isoformat() + "Z",
    }


def seed_victim(client: BackendClient, victim_config: dict, verbose: bool = True):
    vid = victim_config["id"]
    traj = victim_config["trajectory"]
    n = victim_config["n_checkins"]
    trigger_at = victim_config.get("trigger_at")
    eval_alert_at = victim_config.get("evaluate_alert_at")
    desc = victim_config["description"]

    print(f"\n{'─'*70}")
    print(f"  🎭 {desc}")
    print(f"     ID: {vid} | Trajectory: {traj.upper()} | {n} check-ins")
    print(f"{'─'*70}")

    # 1. Create victim
    victim_payload = {
        "id": vid,
        "case_type": victim_config["case_type"],
        "assigned_district": victim_config["assigned_district"],
        "assigned_state": victim_config["assigned_state"],
        "consent_flag": victim_config["consent_flag"],
        "assigned_counsellor_id": victim_config.get("assigned_counsellor_id"),
    }
    result = client.create_victim(victim_payload)
    if result is None:
        print(f"  ❌ Skipping {vid} — victim creation failed.")
        return

    # 2. Build severity curve
    if traj == "gradual_decline":
        severities = gradual_decline_trajectory(n, start=3.0, end=8.8)
    elif traj == "sudden_trigger":
        t = trigger_at if trigger_at is not None else n // 2
        severities = sudden_trigger_trajectory(n, trigger_at=t)
    elif traj == "stable_low":
        severities = stable_low_trajectory(n)
    elif traj == "recovery":
        severities = recovery_trajectory(n, start=8.2, end=2.0)
    elif traj == "moderate_decline":
        severities = moderate_decline_trajectory(n)
    else:
        severities = [5.0] * n

    # 3. Generate timestamps (spread over 2 months)
    timestamps = generate_timestamps(n, span_days=60)

    # 4. Post check-ins
    scores_logged = []
    for i, (severity, ts) in enumerate(zip(severities, timestamps)):
        payload = build_checkin_payload(
            victim_id=vid,
            turn_index=i,
            n_turns=n,
            trajectory_name=traj,
            severity=severity,
            timestamp=ts,
            trigger_at=trigger_at,
        )

        response = client.create_check_in(payload)
        actual_score = response.get("distress_score") if response else payload["distress_score"]
        scores_logged.append(actual_score or payload["distress_score"])

        is_trigger = trigger_at is not None and i == trigger_at
        icon = "⚡" if is_trigger else "  "
        print(
            f"   {icon} T{i+1:02d} [{ts.strftime('%d %b')}] "
            f"Channel: {payload['channel']:8s} | "
            f"Severity: {severity:.1f} | "
            f"Score: {payload['distress_score']:5.1f} | "
            f"{payload['emotion_label']:20s} | "
            f"{payload['raw_text'][:50]}…" if len(payload['raw_text']) > 50 else
            f"   {icon} T{i+1:02d} [{ts.strftime('%d %b')}] "
            f"Channel: {payload['channel']:8s} | "
            f"Severity: {severity:.1f} | "
            f"Score: {payload['distress_score']:5.1f} | "
            f"{payload['emotion_label']:20s}"
        )

        # 5. Evaluate alert at specified turn
        if eval_alert_at is not None and i == eval_alert_at - 1:
            print(f"\n   🚨 Evaluating alert for {vid} at turn {i+1}…")
            time.sleep(0.5)  # Small delay before ML call
            alert_result = client.evaluate_alert(vid)
            if alert_result:
                if "alert_id" in alert_result and alert_result["alert_id"]:
                    print(f"   🚨 ALERT TRIGGERED! ID={alert_result['alert_id']} | "
                          f"Risk={alert_result.get('risk_level')} | "
                          f"Score={alert_result.get('distress_score')}")
                else:
                    print(f"   ℹ  No alert threshold crossed yet (score={alert_result.get('distress_score')})")
            print()

        time.sleep(0.2)  # Rate-limit API calls

    # Summary
    avg = sum(scores_logged) / len(scores_logged) if scores_logged else 0
    peak = max(scores_logged) if scores_logged else 0
    trend_val = scores_logged[-1] - scores_logged[0] if len(scores_logged) >= 2 else 0
    trend = "↑ worsening" if trend_val > 8 else "↓ improving" if trend_val < -8 else "→ stable"
    print(f"\n   ✅ Done: avg={avg:.1f} | peak={peak:.1f} | trend={trend}")


# ─── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="MindGuard Synthetic Demo Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--backend", default=BACKEND_URL, help="Backend base URL")
    parser.add_argument("--username", default="district_patna", help="Login username")
    parser.add_argument("--password", default="password123", help="Login password")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without calling API")
    parser.add_argument("--victim", help="Seed only this victim ID (e.g. VIC-2024-10002)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    random.seed(args.seed)

    print("\n" + "═" * 70)
    print("  MindGuard — Synthetic Demo Data Generator")
    print("  SIH · NHAA 14566 · Prototype only — all data is synthetic")
    print("═" * 70)

    if args.dry_run:
        print("\n  ⚠  DRY RUN MODE — no API calls will be made.\n")

    client = BackendClient(base_url=args.backend, dry_run=args.dry_run)

    # Authenticate
    if not client.login(args.username, args.password):
        print("\n❌ Cannot proceed without authentication. Is the backend running?")
        print(f"   Backend URL: {args.backend}")
        sys.exit(1)

    # Filter victims if --victim flag passed
    victims_to_seed = [
        v for v in VICTIMS
        if args.victim is None or v["id"] == args.victim
    ]

    if not victims_to_seed:
        print(f"❌ No victim found matching '{args.victim}'")
        sys.exit(1)

    print(f"\n📋 Seeding {len(victims_to_seed)} victim(s) with synthetic check-ins…")

    for victim_config in victims_to_seed:
        seed_victim(client, victim_config, verbose=True)

    # Final evaluation pass — trigger alerts for all high-risk victims
    print(f"\n{'═'*70}")
    print("  🔍 Final alert evaluation pass for high-risk victims…")
    print(f"{'═'*70}")

    high_risk_victims = [v for v in victims_to_seed if v.get("evaluate_alert_at") is not None]
    for vc in high_risk_victims:
        print(f"\n  📊 Evaluating {vc['id']} ({vc['trajectory'].replace('_', ' ').title()})…")
        result = client.evaluate_alert(vc["id"])
        if result and "alert_id" in result and result["alert_id"]:
            print(f"  🚨 ALERT CONFIRMED: {vc['id']} | Risk={result.get('risk_level')} | "
                  f"Score={result.get('distress_score')} | EscProb={result.get('escalation_probability')}")
        elif result:
            print(f"  ℹ  {vc['id']}: Score={result.get('distress_score')} (below threshold)")
        time.sleep(1)

    print(f"\n{'═'*70}")
    print("  ✅ Demo dataset generation complete!")
    print()
    print("  Dashboard: http://localhost:3000/dashboard")
    print("  API docs:  http://localhost:8000/docs")
    print("  Alerts:    http://localhost:3000/alerts")
    print()
    print("  Victims created:")
    for v in victims_to_seed:
        icon = "🚨" if v.get("evaluate_alert_at") else "✅"
        print(f"   {icon}  {v['id']}  {v['trajectory']:20s}  {v['description'].split('—')[0].strip()}")
    print(f"{'═'*70}\n")


if __name__ == "__main__":
    main()
