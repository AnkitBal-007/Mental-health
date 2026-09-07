# ML Pipeline — Distress Monitoring AI Service

> **⚠ Prototype — Synthetic Data Only**
> All models are pre-trained on public data. No real victim data is used at any stage.

FastAPI service that powers the AI layer of the mental health distress-monitoring system. Runs on **port 8001**.

## Architecture

```
schemas/          Pydantic request/response models
services/         Business logic (one file per capability)
  text_analyzer   Multilingual sentiment + emotion (HuggingFace)
  voice_analyzer  Whisper transcription + librosa prosodic features
  distress_scorer Rule-based scoring formula (swap-ready for trained model)
  escalation_predictor  Scikit-Learn Gradient Boosting on synthetic longitudinal data
  synthetic_trajectory_generator  Realistic longitudinal trajectory dataset generator
routers/          FastAPI route handlers (thin — delegate to services)
config.py         All settings (env-overridable)
main.py           App entrypoint + lifespan model loading
```

## Models Used

| Capability | Model | Type | Multilingual |
|---|---|---|---|
| Sentiment | `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` | Pre-trained transformer | ✅ Hindi + English + 6 more |
| Emotion | `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` | Zero-shot NLI classification | ✅ 100+ languages |
| Transcription | OpenAI Whisper (`base`) | Pre-trained speech-to-text | ✅ 99 languages |
| Distress scoring | Custom weighted formula | **Rule-based** (not ML) | N/A |
| Escalation prediction | Scikit-Learn `GradientBoostingClassifier` | Trained on **synthetic trajectories** | N/A |

## Setup

### Prerequisites

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/download.html) installed and on PATH (required by Whisper)

### Install

```bash
cd ml-pipeline
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Run

```bash
# Development (auto-reload)
python main.py

# Or directly with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

The first run will download models from HuggingFace (~1-2 GB total). Subsequent starts use the cache.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ML_PIPELINE_PORT` | `8001` | Server port |
| `ML_PIPELINE_HOST` | `0.0.0.0` | Server host |
| `SENTIMENT_MODEL` | `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` | HuggingFace sentiment model |
| `EMOTION_MODEL` | `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` | HuggingFace NLI model for emotion |
| `WHISPER_MODEL_SIZE` | `base` | Whisper model size (tiny/base/small/medium/large) |

---

## API Endpoints

Interactive docs available at: **http://localhost:8001/docs**

---

### `POST /analyze/text` — Text Sentiment & Emotion Analysis

Analyzes text for sentiment (positive/neutral/negative) and emotion classification (fear, sadness, anger, calm, distress, anxiety, hope, neutral).

**Request:**

```json
{
  "text": "I feel very scared and alone after the hearing.",
  "language": "en"
}
```

**Example curl:**

```bash
curl -X POST http://localhost:8001/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "I feel very scared and alone after the hearing.", "language": "en"}'
```

**Hindi example:**

```bash
curl -X POST http://localhost:8001/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "मुझे बहुत डर लग रहा है और मैं अकेला महसूस कर रहा हूँ", "language": "hi"}'
```

**Response:**

```json
{
  "sentiment": {
    "label": "negative",
    "confidence": 0.8923
  },
  "emotions": [
    {"label": "fear", "score": 0.4512},
    {"label": "sadness", "score": 0.2837},
    {"label": "distress", "score": 0.1204},
    {"label": "anxiety", "score": 0.0891},
    {"label": "anger", "score": 0.0234},
    {"label": "neutral", "score": 0.0156},
    {"label": "calm", "score": 0.0098},
    {"label": "hope", "score": 0.0068}
  ],
  "language": "en",
  "text_length": 48
}
```

---

### `POST /analyze/voice` — Voice Transcription & Stress Features

Accepts an audio file upload. Returns Whisper transcript, prosodic features, and rule-based stress indicators.

**Example curl:**

```bash
curl -X POST http://localhost:8001/analyze/voice \
  -F "file=@checkin_audio.wav"
```

**Response:**

```json
{
  "transcript": "I have not been sleeping well since the incident.",
  "language_detected": "en",
  "duration_seconds": 4.82,
  "prosodic_features": {
    "pitch_mean_hz": 187.34,
    "pitch_variance": 3421.56,
    "speaking_rate_syllables_per_sec": 3.12,
    "pause_ratio": 0.2847,
    "energy_mean": 0.042315,
    "energy_variance": 0.00134200
  },
  "stress_indicators": {
    "pitch_elevated": true,
    "speech_rate_abnormal": false,
    "high_pause_ratio": false,
    "energy_irregular": false,
    "overall_stress_level": "moderate"
  }
}
```

**Supported audio formats:** WAV, MP3, OGG, FLAC, M4A, WebM (max 25 MB).

---

### `POST /score/distress` — Dynamic Distress Score

Takes a list of recent interaction records for one victim and computes a Dynamic Distress Score (0–100), trend direction, and a plain-language factor breakdown.

**Request:**

```json
{
  "victim_id": "VIC-2024-00483",
  "interactions": [
    {
      "sentiment_score": 0.2,
      "emotion_label": "neutral",
      "engagement_score": 1.0,
      "timestamp": "2024-12-01T10:00:00Z",
      "check_in_type": "chatbot"
    },
    {
      "sentiment_score": -0.3,
      "emotion_label": "sadness",
      "engagement_score": 0.8,
      "timestamp": "2024-12-04T10:00:00Z",
      "check_in_type": "chatbot"
    },
    {
      "sentiment_score": -0.6,
      "emotion_label": "fear",
      "engagement_score": 0.6,
      "timestamp": "2024-12-07T10:00:00Z",
      "check_in_type": "ivrs"
    },
    {
      "sentiment_score": -0.8,
      "emotion_label": "distress",
      "engagement_score": 0.4,
      "timestamp": "2024-12-10T10:00:00Z",
      "check_in_type": "chatbot"
    }
  ]
}
```

**Example curl:**

```bash
curl -X POST http://localhost:8001/score/distress \
  -H "Content-Type: application/json" \
  -d '{
    "victim_id": "VIC-2024-00483",
    "interactions": [
      {"sentiment_score": 0.2, "emotion_label": "neutral", "engagement_score": 1.0, "timestamp": "2024-12-01T10:00:00Z", "check_in_type": "chatbot"},
      {"sentiment_score": -0.3, "emotion_label": "sadness", "engagement_score": 0.8, "timestamp": "2024-12-04T10:00:00Z", "check_in_type": "chatbot"},
      {"sentiment_score": -0.6, "emotion_label": "fear", "engagement_score": 0.6, "timestamp": "2024-12-07T10:00:00Z", "check_in_type": "ivrs"},
      {"sentiment_score": -0.8, "emotion_label": "distress", "engagement_score": 0.4, "timestamp": "2024-12-10T10:00:00Z", "check_in_type": "chatbot"}
    ]
  }'
```

**Response:**

```json
{
  "victim_id": "VIC-2024-00483",
  "distress_score": 72.4,
  "trend": "worsening",
  "trend_detail": "Distress indicators increased by 18.3 points over the last 4 check-ins",
  "confidence": 0.4,
  "factors": [
    {
      "factor": "Emotional state",
      "contribution": 24.1,
      "detail": "Predominant recent emotion: distress, contributing ~24 points"
    },
    {
      "factor": "Sentiment pattern",
      "contribution": 22.0,
      "detail": "Recent sentiment is negative (latest score: -0.80), contributing ~22 points"
    },
    {
      "factor": "Engagement decline",
      "contribution": 4.5,
      "detail": "Low engagement detected in recent check-ins, contributing ~5 points"
    }
  ],
  "interactions_analyzed": 4,
  "computed_at": "2024-12-10T12:34:56.789Z"
}
```

---

### `POST /explain/distress` — Explainability Breakdown

Same input as `/score/distress`. Returns the distress score **plus** a granular, ranked breakdown of contributing factors with point contributions that sum to the total score. Each factor is a `{factor, contribution, description}` object the frontend can render directly.

**Current scoring method:** `rule-based` (transparent weighted breakdown).
When a trained model (XGBoost/scikit-learn) is used, this switches to SHAP-based explanations.

**Example curl:**

```bash
curl -X POST http://localhost:8001/explain/distress \
  -H "Content-Type: application/json" \
  -d '{
    "victim_id": "VIC-2024-00483",
    "interactions": [
      {"sentiment_score": 0.2, "emotion_label": "neutral", "engagement_score": 1.0, "timestamp": "2024-12-01T10:00:00Z", "check_in_type": "chatbot"},
      {"sentiment_score": -0.3, "emotion_label": "sadness", "engagement_score": 0.8, "timestamp": "2024-12-04T10:00:00Z", "check_in_type": "chatbot"},
      {"sentiment_score": -0.6, "emotion_label": "fear", "engagement_score": 0.6, "timestamp": "2024-12-07T10:00:00Z", "check_in_type": "ivrs"},
      {"sentiment_score": -0.8, "emotion_label": "distress", "engagement_score": 0.4, "timestamp": "2024-12-10T10:00:00Z", "check_in_type": "chatbot"}
    ]
  }'
```

**Response:**

```json
{
  "victim_id": "VIC-2024-00483",
  "distress_score": 72.4,
  "trend": "worsening",
  "trend_detail": "Distress indicators increased by 18.3 points over the last 4 check-ins",
  "scoring_method": "rule-based",
  "factors": [
    {
      "factor": "Declining sentiment trend",
      "contribution": 18.2,
      "description": "Sentiment declined by +0.55 (from -0.05 avg to -0.70 avg) across 4 check-ins: +18 points"
    },
    {
      "factor": "Negative emotion predominance",
      "contribution": 15.4,
      "description": "3 of 4 check-ins showed distressing emotions (most common: fear): +15 points"
    },
    {
      "factor": "Latest check-in severity",
      "contribution": 13.8,
      "description": "Most recent check-in: sentiment -0.80, emotion 'distress' (weight 0.95): +14 points"
    },
    {
      "factor": "Current sentiment level",
      "contribution": 12.1,
      "description": "Average recent sentiment is negative (score: -0.57): +12 points"
    },
    {
      "factor": "High emotional volatility",
      "contribution": 9.3,
      "description": "Emotions shifted 3 times across 4 different states in 4 check-ins (volatility: 100%): +9 points"
    },
    {
      "factor": "Engagement decline",
      "contribution": 3.6,
      "description": "Engagement dropped from 0.90 avg to 0.50 avg over 4 check-ins: +4 points"
    }
  ],
  "confidence": 0.4,
  "interactions_analyzed": 4,
  "computed_at": "2024-12-10T12:34:56.789Z"
}
```

**Factor types detected:**

| Factor | Max Points | When it triggers |
|---|---|---|
| Current sentiment level | 20 | Always (based on last 3 check-ins) |
| Declining sentiment trend | 18 | When sentiment is getting worse over time |
| Negative emotion predominance | 20 | Always (ratio of distressing emotions) |
| High emotional volatility | 12 | When emotions switch > 30% of the time |
| Latest check-in severity | 15 | Always (based on most recent check-in) |
| Missed check-ins | 12 | When engagement < 0.3 on any check-in |
| Engagement decline | 8 | When engagement is trending downward |

---

### `POST /predict/escalation` — Distress Escalation Prediction

> **Synthetic Data Notice:**
> This model is trained on a synthetic longitudinal dataset generating realistic trajectory patterns (gradual decline, sudden trigger spikes, recovering trends, stable low-risk) specifically for prototype testing. No real victim data was used.

Takes a time-series history of past distress scores with timestamps for a victim and predicts the probability of significant distress escalation occurring in the upcoming check-in window (default: 7 days).

**Request:**

```json
{
  "victim_id": "VIC-2024-00483",
  "history": [
    { "distress_score": 32.0, "timestamp": "2024-11-20T10:00:00Z" },
    { "distress_score": 38.5, "timestamp": "2024-11-24T10:00:00Z" },
    { "distress_score": 52.0, "timestamp": "2024-11-28T10:00:00Z" },
    { "distress_score": 68.0, "timestamp": "2024-12-02T10:00:00Z" }
  ],
  "prediction_window_days": 7
}
```

**Example curl:**

```bash
curl -X POST http://localhost:8001/predict/escalation \
  -H "Content-Type: application/json" \
  -d '{
    "victim_id": "VIC-2024-00483",
    "history": [
      {"distress_score": 32.0, "timestamp": "2024-11-20T10:00:00Z"},
      {"distress_score": 38.5, "timestamp": "2024-11-24T10:00:00Z"},
      {"distress_score": 52.0, "timestamp": "2024-11-28T10:00:00Z"},
      {"distress_score": 68.0, "timestamp": "2024-12-02T10:00:00Z"}
    ],
    "prediction_window_days": 7
  }'
```

**Response:**

```json
{
  "victim_id": "VIC-2024-00483",
  "escalation_probability": 0.8842,
  "risk_level": "high",
  "escalation_likely": true,
  "predicted_trend": "sharp_increase",
  "summary": "High risk of acute distress escalation (probability: 88%) within the next 7 days. Trajectory shows sharp increase with current score at 68. Early counsellor outreach recommended.",
  "key_signals": [
    {
      "feature": "Current Distress Level",
      "value": 68.0,
      "impact": "Latest recorded score is 68.0/100 (elevated)."
    },
    {
      "feature": "Recent Trajectory Velocity",
      "value": 12.3,
      "impact": "Distress is trending upward (+12.3 pts/check-in)."
    },
    {
      "feature": "Last Check-in Shift",
      "value": 16.0,
      "impact": "Score shifted by +16.0 points between the last two interactions."
    }
  ],
  "data_points_analyzed": 4,
  "model_provenance": "Synthetic longitudinal dataset (Scikit-Learn Gradient Boosting Classifier)",
  "computed_at": "2024-12-02T12:00:00Z"
}
```

**Synthetic Trajectory Patterns in Training Data:**

1. **Gradual Decline:** Distress score steadily climbs (+2.5 to +6 pts per check-in) over weeks due to prolonged litigation, trial delays, or social isolation.
2. **Sudden Trigger Spike:** Baseline was stable, but a sudden threat, intimidation, or court appearance triggers an abrupt +25 to +40 jump.
3. **Stable Low-Risk:** Resilient baseline where scores gently fluctuate between 15–35 without escalation.
4. **Recovering Trend:** Initial acute distress (70–90) steadily resolves downward (20–35) with support and rehabilitation.
5. **High-Risk Volatile:** High average baseline (65–85) with erratic oscillations.

---

### `GET /health` — Readiness Check

```bash
curl http://localhost:8001/health
```

```json
{
  "status": "ok",
  "text_analyzer_loaded": true,
  "voice_analyzer_loaded": true,
  "escalation_predictor_loaded": true
}
```

---

## Scoring Formula (Distress Scorer)

The scoring logic lives in [`services/distress_scorer.py`](services/distress_scorer.py) in the `compute_distress_score()` function. It is **rule-based** (not ML-trained) and designed to be swapped for a trained model (e.g. XGBoost) when longitudinal data becomes available.

### Breakdown (max 100 points)

| Component | Max Points | Input |
|---|---|---|
| Sentiment | 40 | Negative sentiment → higher score |
| Emotion | 35 | High-distress emotions (fear, distress, anxiety) → higher score |
| Engagement | 15 | Low engagement / short responses → higher score |
| Missed check-ins | 10 | Penalty for very low engagement (< 0.3) |

All components are **recency-weighted** — recent check-ins have more influence than older ones.

### Trend Detection

Compares the average distress proxy of the first half vs. second half of the last N check-ins:
- **Worsening**: second half is >5 points higher
- **Improving**: second half is >5 points lower
- **Stable**: difference is within ±5 points

### Swapping the Scorer

To replace with a trained model:

1. Edit `compute_distress_score()` in `services/distress_scorer.py`
2. Keep the same function signature: `List[InteractionRecord] → Dict`
3. Keep the same return keys: `distress_score`, `factors`, `confidence`, `interactions_analyzed`
4. Edit `explain_distress_score()` to use SHAP for the explainability breakdown:
   ```python
   import shap
   explainer = shap.TreeExplainer(model)
   shap_values = explainer.shap_values(features)
   # Map SHAP values to {factor, contribution, description} dicts
   ```
5. Update `scoring_method` return value from `"rule-based"` to `"model-based (SHAP)"`
6. The routers and schemas don't need to change

---

## Project Rules Compliance

- ✅ Every score ships with a factor breakdown — no bare numbers
- ✅ Scoring formula is rule-based and fully inspectable
- ✅ Synthetic data only — no real victim data
- ✅ Models documented (this README)
- ✅ No hardcoded secrets — all config via environment variables
