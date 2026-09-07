# PRD — AI-Powered Dynamic Mental Health Monitoring and Distress Prediction System

## 1. Problem

Victims registered through NHAA (14566), the Integrated Portal, chatbot, mobile app, IVRS, or other approved channels frequently experience prolonged psychological distress after filing a complaint — from threats, intimidation, repeated court appearances, trial delays, social ostracism, economic hardship, and rehabilitation challenges. Existing mechanisms cover legal and financial support but do not continuously monitor victim well-being.

## 2. Goal

Build a system that continuously monitors and predicts psychological distress among victims and complainants throughout investigation, trial, rehabilitation, and compensation — and surfaces early warnings to counsellors and officials before a crisis emerges.

## 3. Users

| User | Need |
|---|---|
| Victim / complainant | A low-friction way to check in (chatbot, IVRS, SMS, app) without needing to self-report distress explicitly |
| Counsellor | A prioritized queue of at-risk victims with clear reasoning, not just a raw score |
| District official | Visibility into all monitored cases in their district, and the ability to assign/act on alerts |
| State / national official | Aggregated trend visibility for policy and resourcing decisions |

## 4. Core features (MVP scope for hackathon)

1. **Multi-channel check-ins** — chatbot (real) + simulated IVRS/SMS logs feeding the same pipeline.
2. **Sentiment & emotion analysis** — multilingual (Hindi + English minimum) NLP on text; voice-stress features on audio.
3. **Dynamic Distress Score** — 0–100 score per victim, recomputed each check-in, with a visible trend (improving / stable / worsening).
4. **Escalation prediction** — model estimates probability of significant distress escalation before the next check-in.
5. **Explainability** — every score shows the top contributing factors in plain language (not just a number).
6. **Threshold-based alerts** — auto-generated when score or predicted escalation crosses a configurable threshold; routed to a counsellor queue.
7. **Recommended interventions** — rules-based mapping from risk profile + case type to suggested actions (counselling, medical, protection, relocation, financial, legal aid).
8. **Role-based dashboards** — district / state / national views, filtered by scope.

## 5. Out of scope for hackathon prototype

- Real IVRS/SMS telecom integration (simulated instead)
- Training on real victim data (synthetic data only)
- Formal security/compliance certification
- Native mobile app (responsive web covers this)

## 6. Success criteria (for demo)

- One synthetic victim journey visibly shows: declining sentiment → rising distress score → explanation → triggered alert → recommended intervention, end to end with no manual intervention.
- Dashboard clearly differentiates district / state / national views.
- Every distress score displayed is accompanied by an explanation, never a bare number.

## 7. Constraints

- Must support at least Hindi and English.
- Every automated decision (score, alert, recommendation) must be explainable — no black-box outputs in the UI.
- No feature may auto-execute an intervention; a human always makes the final call.
- Victim identifiers shown in dashboards must be anonymized/pseudonymized.

## 8. Priority use cases

- Victims of rape and gang rape
- Victims of murder, grievous hurt, and arson
- Witnesses facing intimidation or threats
- Families affected by caste-based violence
- Beneficiaries under the SC/ST (Prevention of Atrocities) Act, 1989
