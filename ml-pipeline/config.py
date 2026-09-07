"""
Configuration for the ML Pipeline service.

All settings can be overridden via environment variables.
"""

import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------

# Model configuration
# ---------------------------------------------------------------------------
SENTIMENT_MODEL = os.getenv(
    "SENTIMENT_MODEL",
    "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
)
EMOTION_MODEL = os.getenv(
    "EMOTION_MODEL",
    "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
)
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# ---------------------------------------------------------------------------
# Distress scoring
# ---------------------------------------------------------------------------
DISTRESS_SCORE_WINDOW = int(os.getenv("DISTRESS_SCORE_WINDOW", "10"))
TREND_WINDOW = int(os.getenv("TREND_WINDOW", "5"))

# Emotion labels for zero-shot classification
EMOTION_LABELS = [
    "fear",
    "sadness",
    "anger",
    "calm",
    "distress",
    "anxiety",
    "hope",
    "neutral",
]

# ---------------------------------------------------------------------------
# Server & Network
# ---------------------------------------------------------------------------
HOST = os.getenv("ML_PIPELINE_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT") or os.getenv("ML_PIPELINE_PORT") or "8001")

_origins_env = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS") or ""
if _origins_env.strip():
    ALLOWED_ORIGINS = [origin.strip() for origin in _origins_env.split(",") if origin.strip()]
else:
    ALLOWED_ORIGINS = ["http://localhost:3000"]

# ---------------------------------------------------------------------------
# Conversational AI (Google Gemini)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


