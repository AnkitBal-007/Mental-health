# MindGuard — Simulation & Demo Data Generator

## Overview

This directory contains the synthetic data generator that populates the backend database
with realistic longitudinal victim check-in data for demonstration purposes.

> **All data is synthetic.** No real victim information is used or stored.

---

## Quick Start

Make sure the backend is running at `http://localhost:8000` first:

```powershell
# In /backend
py main.py
```

Then run the generator:

```powershell
# In /simulation
$env:PYTHONIOENCODING="utf-8"
py generate_demo_data.py
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--backend` | `http://localhost:8000` | Backend API base URL |
| `--username` | `district_patna` | Login username |
| `--password` | `password123` | Login password |
| `--dry-run` | — | Print payloads without calling the API |
| `--victim` | — | Seed only one victim (e.g. `--victim VIC-2024-10002`) |
| `--seed` | `42` | Random seed for reproducibility |

### Examples

```powershell
# Full demo dataset (all 6 victims)
py generate_demo_data.py

# Preview what would be sent (no API calls)
py generate_demo_data.py --dry-run

# Only seed the high-risk victim
py generate_demo_data.py --victim VIC-2024-10002

# Use a different user account
py generate_demo_data.py --username national_admin --password password123
```

---

## Victims & Trajectories

| Victim ID | Name | Case Type | Trajectory | Alert? |
|---|---|---|---|---|
| `VIC-2024-10001` | Sunita Devi | atrocity_act | 🌱 Recovery | — |
| `VIC-2024-10002` | Priya Sharma | sexual_violence | 📉 Gradual Decline | 🚨 Yes (turn 9) |
| `VIC-2024-10003` | Kavita Rani | intimidation | ⚡ Sudden Trigger | 🚨 Yes (turn 8) |
| `VIC-2024-10004` | Radha Singh | murder_witness | ✅ Stable Low Risk | — |
| `VIC-2024-10005` | Meena Devi | caste_based_violence | 📉 Moderate Decline | — |
| `VIC-2024-10006` | Poonam Kumari | grievous_hurt | 🌱 Recovery | — |

---

## How it Works

Each victim gets **10–15 check-ins** spread across a simulated **60-day period**:

1. **Creates victim** via `POST /victims`
2. **Posts check-ins** via `POST /check-ins` with:
   - Realistic English/Hindi text responses matching the emotional trajectory
   - Computed `sentiment_score`, `emotion_label`, `distress_score`, `engagement_score`
   - Channels: `chatbot`, `sms`, `ivrs`, `portal`
   - Timestamps distributed realistically across 2 months
3. **Evaluates alerts** via `POST /alerts/evaluate` at critical turns

For `VIC-2024-10002` (gradual decline) and `VIC-2024-10003` (sudden trigger), the
distress score crosses the alert threshold (70), and the backend calls the ML pipeline
to trigger a real alert record visible in the dashboard.

---

## Trajectory Formulas

| Pattern | Severity Curve |
|---|---|
| Gradual Decline | Linear 3.0 → 8.8 over N turns |
| Sudden Trigger | Stable ~3.0, spike to ~9.5 at turn 7, stays elevated |
| Stable Low Risk | Uniform random 1.5–3.5 |
| Recovery | Linear 8.2 → 2.0 over N turns |
| Moderate Decline | Slow increase staying in 3–7 range |

---

## After Running

- **Dashboard**: http://localhost:3000/dashboard — new victims appear in the table
- **Alerts feed**: http://localhost:3000/alerts — 1–2 triggered alerts visible
- **Simulation page**: http://localhost:3000/simulation — run interactive trajectory replays
- **API docs**: http://localhost:8000/docs
