# Architecture

## Overview

Four layers, with security/privacy running across all of them:

```
Input channels → AI processing → Risk & alert engine → Dashboards
                        (security/privacy layer spans all four)
```

## 1. Input channels

- **Chatbot** (real, built in `/chatbot`) — web widget, text-based, English + Hindi.
- **IVRS calls** — simulated for the prototype via `/simulation`; represents voice check-ins.
- **SMS** — simulated for the prototype via `/simulation`.
- **Mobile app / web portal** — the responsive dashboard/chatbot serves this role for the prototype; a native app is out of scope.
- **Helpline follow-up** — represented conceptually, not built.

All channels write to the same `check_ins` table via the backend API, regardless of origin.

## 2. AI processing (`/ml-pipeline`, FastAPI, port 8001)

- **Text analysis** (`POST /analyze/text`) — multilingual sentiment + emotion classification (MuRIL/IndicBERT-class model).
- **Voice analysis** (`POST /analyze/voice`) — Whisper transcription + librosa-based prosodic features (pitch variance, speaking rate, pause ratio, energy).
- **Distress scoring** (`POST /score/distress`) — combines recent check-ins into a single 0–100 score plus trend direction.
- **Explainability** (`POST /explain/distress`) — returns the score with a ranked, human-readable factor breakdown (SHAP where a trained model is used, otherwise a transparent weighted rule breakdown).
- **Escalation prediction** (`POST /predict/escalation`) — gradient-boosted model (XGBoost/scikit-learn) trained on synthetic longitudinal data, predicts probability of escalation before the next check-in.

## 3. Risk & alert engine (`/backend`, FastAPI, port 8000)

- Stores victims, check-ins, alerts, and users (PostgreSQL, SQLAlchemy models).
- `POST /alerts/evaluate` — calls the ML pipeline, checks score/escalation against configurable thresholds, creates an alert if crossed.
- `GET /victims/{id}/recommendations` — rules-table lookup mapping risk profile + case type to suggested interventions (counselling, medical, protection, relocation, financial, legal aid). Stored as an editable JSON config, not hardcoded.
- JWT auth with role claims: `district`, `state`, `national`, `counsellor`.

## 4. Dashboards (`/frontend`, React + Tailwind, port 3000)

- Login (role-based).
- Victim list — sortable/filterable by risk level and district.
- Victim detail — distress score trend chart (recharts), factor breakdown, recommended interventions.
- Alerts feed — live list with assign-to-counsellor action.
- Summary stats bar — total monitored, active high-risk cases, alerts this week.

## Cross-cutting: security & privacy

- Encryption in transit (HTTPS) and at rest.
- Anonymized/pseudonymized victim IDs in all views and logs.
- Consent flag stored per victim; opt-out honored at the data-collection layer, not just the UI.
- Role-based access control enforced server-side (not just hidden in the UI).
- Audit log of every dashboard action that touches victim data.

## Data flow (single check-in)

1. Victim responds via chatbot/IVRS/SMS →
2. Backend stores raw check-in →
3. Backend calls ML pipeline `/analyze/text` or `/analyze/voice` →
4. Backend calls `/score/distress` and `/predict/escalation` →
5. Backend evaluates thresholds → creates alert if crossed →
6. Dashboard reflects updated score, trend, and any new alert in near real time.

## Service ports (local dev)

| Service | Port |
|---|---|
| ML pipeline | 8001 |
| Backend API | 8000 |
| Frontend | 3000 |
