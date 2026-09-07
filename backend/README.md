# Case Management Backend — Distress Monitoring System

> **⚠ Prototype — Synthetic Data Only**
> This backend manages anonymized victim cases and handles multi-channel check-in streams. No real personal identifying information (PII) is stored or processed.

FastAPI backend providing PostgreSQL/SQLite persistence, JWT authentication with role-based jurisdictional scoping (`district`, `state`, `national`, `counsellor`), ML pipeline integration, proactive alert evaluation, and intervention recommendation workflows.

Runs on **port 8000**.

---

## 🏛️ Database Schema (SQLAlchemy Models)

| Table | Primary Key | Description |
|---|---|---|
| `users` | `id` (int) | System users with role claims (`district`, `state`, `national`, `counsellor`) and assigned jurisdictions. |
| `victims` | `id` (string, e.g. `VIC-2024-001`) | **Anonymized** victim case records, case types (Atrocities Act, intimidation, etc.), and cached risk metrics. |
| `check_ins` | `id` (int) | Multi-channel interaction records (Chatbot, IVRS, SMS, Portal) with sentiment, emotion, and distress metrics. |
| `alerts` | `id` (int) | Generated alerts when safety thresholds are breached, containing SHAP explainability factors and recommended interventions. |
| `audit_logs` | `id` (int) | Immutable audit trail tracking every official action and access to sensitive victim case records. |

---

## 🚀 Setup & Execution

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Seed Database (Demo Users & Synthetic Trajectories)

```bash
python seed_data.py
```

### 3. Run the Backend Service

```bash
python main.py
# Or with uvicorn:
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive Swagger UI: **http://localhost:8000/docs**

---

## 👥 Demo User Accounts

All pre-seeded demo accounts share the password: **`password123`**

| Username | Role | Jurisdiction | Use Case |
|---|---|---|---|
| `national_admin` | `national` | All India | Nationwide aggregates, cross-state policy visibility. |
| `state_bihar` | `state` | Bihar | State-level view, drill-down into Bihar districts. |
| `district_patna` | `district` | Patna (Bihar) | District-level case queue and alert management. |
| `counsellor_priya` | `counsellor` | Patna (Bihar) | At-risk victim queue, intervention confirmation. |

---

## 🔑 Authentication & Role Scoping

Obtain a JWT token via `POST /auth/login` and pass it in the `Authorization: Bearer <token>` header:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "district_patna", "password": "password123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "role": "district",
  "district": "Patna",
  "state": "Bihar",
  "username": "district_patna"
}
```

---

## 📡 Key API Endpoints

### 1. Alert Evaluation (`POST /alerts/evaluate`)

Triggers a live evaluation of a victim's check-in trajectory against the ML Pipeline (at `http://localhost:8001`). If distress score $\ge 70$ or escalation probability $\ge 60\%$, an alert is automatically created.

```bash
curl -X POST http://localhost:8000/alerts/evaluate \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"victim_id": "VIC-2024-00483"}'
```

**Response:**
```json
{
  "victim_id": "VIC-2024-00483",
  "alert_created": true,
  "distress_score": 82.0,
  "trend": "worsening",
  "escalation_probability": 0.92,
  "risk_level": "high",
  "alert": {
    "id": 1,
    "victim_id": "VIC-2024-00483",
    "risk_level": "critical",
    "status": "open",
    "distress_score": 82.0,
    "escalation_probability": 0.92,
    "trigger_reason": "Distress score (82.0) crossed threshold (70.0); Escalation probability (92%) crossed safety limit (60%)"
  },
  "explanation": [
    {
      "factor": "Declining sentiment trend",
      "contribution": 22.5,
      "description": "Sentiment dropped sharply from +0.20 to -0.85 across 4 check-ins"
    }
  ],
  "recommended_interventions": [
    {
      "category": "protection",
      "title": "Immediate Threat Assessment & Police Escort",
      "priority": "immediate",
      "recommended_authority": "District Superintendent of Police / Witness Protection Cell"
    }
  ]
}
```

---

### 2. Dashboard Aggregations (`GET /dashboard/summary`)

Aggregates total monitored cases, active alerts, risk distributions, and trends based on scope (`district`, `state`, `national`):

```bash
# District scope
curl -X GET "http://localhost:8000/dashboard/summary?scope=district&id=Patna" \
  -H "Authorization: Bearer <TOKEN>"

# State scope
curl -X GET "http://localhost:8000/dashboard/summary?scope=state&id=Bihar" \
  -H "Authorization: Bearer <TOKEN>"

# National scope
curl -X GET "http://localhost:8000/dashboard/summary?scope=national" \
  -H "Authorization: Bearer <TOKEN>"
```

**Response:**
```json
{
  "scope": "district",
  "scope_id": "Patna",
  "total_monitored_victims": 3,
  "active_alerts": 1,
  "alerts_this_week": 1,
  "average_distress_score": 45.8,
  "high_risk_cases": 1,
  "moderate_risk_cases": 0,
  "low_risk_cases": 2,
  "trend_distribution": {
    "improving": 1,
    "stable": 1,
    "worsening": 1
  }
}
```

---

### 3. Record a Check-in (`POST /check-ins`)

Records a new check-in across Chatbot, IVRS, SMS, or Portal. If raw text is sent without explicit polarity, the backend automatically calls the ML pipeline to analyze sentiment and emotion.

```bash
curl -X POST http://localhost:8000/check-ins \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "victim_id": "VIC-2024-00483",
    "channel": "chatbot",
    "raw_text": "I am feeling very scared after yesterday court appearance.",
    "engagement_score": 0.75
  }'
```

---

### 4. Suggested Interventions (`GET /victims/{id}/recommendations`)

Fetches a transparently ranked list of tailored interventions mapped dynamically from `config/recommendation_rules.json` based on:
1. Dynamic Distress Score (0–100)
2. Contributing psychological & situational factors (fear, threats, volatility, declining sentiment)
3. Legal case type (`rape`, `murder_witness`, `caste_based_violence`, `atrocity_act`, `intimidation`, etc.)

Supported intervention categories:
- `counselling` (Emergency trauma stabilization, weekly psychotherapy, routine wellness)
- `medical` (District Civil Hospital clinical assessment & psychiatric review)
- `protection` (Police escort, perimeter security under Witness Protection Scheme)
- `relocation` (Safe house / One Stop Centre shelter placement)
- `financial` (SC/ST Act interim compensation / State Victim Compensation Scheme)
- `legal_aid` (DLSA pro bono counsel assignment, witness protection petitions)

```bash
curl -X GET http://localhost:8000/victims/VIC-2024-00483/recommendations \
  -H "Authorization: Bearer <TOKEN>"
```

**Response:**
```json
{
  "victim_id": "VIC-2024-00483",
  "case_type": "intimidation",
  "risk_level": "high",
  "current_distress_score": 68.6,
  "escalation_probability": 0.99,
  "contributing_factors_evaluated": [
    "fear",
    "declining sentiment",
    "severe anxiety",
    "low engagement"
  ],
  "total_recommendations": 5,
  "interventions": [
    {
      "category": "protection",
      "title": "Immediate Threat Assessment & Police Escort",
      "description": "Deploy local Special Cell / Police Protection Unit to assess physical perimeter security and provide trial appearance escorts under the Witness Protection Scheme.",
      "priority": "immediate",
      "recommended_authority": "District Superintendent of Police / Witness Protection Cell",
      "ranking_score": 130.2,
      "reason": "Priority justification: Distress score (68.6 >= 65); Matches legal case type 'intimidation'; Triggered by psychological signals: [fear, declining]."
    },
    {
      "category": "legal_aid",
      "title": "Pro Bono Legal Aid & Fast-Track Court Counsel",
      "description": "Assign a designated DLSA retainer advocate to file witness protection petitions, review court summons, and represent the victim in fast-track trial proceedings.",
      "priority": "high",
      "recommended_authority": "District Legal Services Authority (DLSA)",
      "ranking_score": 110.2,
      "reason": "Priority justification: Distress score (68.6 >= 45); Matches legal case type 'intimidation'; Triggered by psychological signals: [sentiment, declining]."
    }
  ],
  "rules_config_source": "config/recommendation_rules.json"
}
```

> **Judge Q&A / Live Demo Customization:**
> The rules are stored in [`backend/config/recommendation_rules.json`](config/recommendation_rules.json). Any adjustments made to thresholds, categories, or authority bodies are reloaded dynamically on every request without restarting the server.


---

### 5. Assign or Resolve Alert (`PATCH /alerts/{id}`)

Assigns an alert to a designated counsellor or marks it resolved with human notes:

```bash
curl -X PATCH http://localhost:8000/alerts/1 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "assigned",
    "assigned_to": 4,
    "resolution_notes": "Assigned to Dr. Priya Sharma for immediate trauma de-escalation call."
  }'
```

---

## 🔒 Security & Privacy Features

1. **Role-Based Access Control (RBAC):** District users cannot see cases outside their district; State users cannot view cases outside their state.
2. **Pseudonymized Victim IDs:** All endpoints only accept/return IDs formatted as `VIC-YYYY-XXXXX`.
3. **Consent Enforcement:** If `consent_flag = False`, check-in data collection is blocked at the API layer.
4. **Audit Logging:** Every query to sensitive victim case data writes an immutable record to the `audit_logs` table.
