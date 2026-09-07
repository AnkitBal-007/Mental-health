"""
ML Pipeline — AI-Powered Distress Monitoring Service
=====================================================

FastAPI service providing text analysis, voice analysis, distress scoring,
and escalation prediction for the mental health monitoring prototype.

Endpoints:
  POST /analyze/text       — Multilingual sentiment + emotion classification
  POST /analyze/voice      — Whisper transcription + prosodic stress features
  POST /score/distress     — Dynamic Distress Score (0–100) with trend & factors
  POST /explain/distress   — Score + ranked factor breakdown for explainability
  POST /predict/escalation — Longitudinal distress escalation prediction
  GET  /health             — Readiness check

Service port: 8001 (configurable via ML_PIPELINE_PORT env var)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import HOST, PORT, ALLOWED_ORIGINS
from routers import text_analysis, voice_analysis, distress_scoring, explainability, escalation, chat_ai
from services.text_analyzer import text_analyzer
from services.voice_analyzer import voice_analyzer
from services.escalation_predictor import escalation_predictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models on startup; clean up on shutdown."""
    logger.info("Starting ML Pipeline — loading models...")

    try:
        text_analyzer.load_models()
    except Exception as e:
        logger.error("Failed to load text analysis models: %s", e)

    try:
        voice_analyzer.load_models()
    except Exception as e:
        logger.error("Failed to load voice analysis models: %s", e)

    try:
        escalation_predictor.train_model()
    except Exception as e:
        logger.error("Failed to train escalation predictor: %s", e)

    logger.info("ML Pipeline ready")
    yield
    logger.info("ML Pipeline shutting down")


app = FastAPI(
    title="Distress Monitoring ML Pipeline",
    description=(
        "AI-powered text analysis, voice analysis, distress scoring, and escalation prediction "
        "for the mental health monitoring prototype.  Part of the SIH project.\n\n"
        "**Models used** (all synthetic-data only, no real victim data):\n"
        "- Sentiment: cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual\n"
        "- Emotion: MoritzLaurer/mDeBERTa-v3-base-mnli-xnli (zero-shot)\n"
        "- Transcription: OpenAI Whisper\n"
        "- Distress scoring: Weighted rule-based formula (see services/distress_scorer.py)\n"
        "- Escalation prediction: Scikit-Learn GradientBoostingClassifier (see services/escalation_predictor.py)"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow configured origins (e.g. Vercel frontend, Render backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(text_analysis.router)
app.include_router(voice_analysis.router)
app.include_router(distress_scoring.router)
app.include_router(explainability.router)
app.include_router(escalation.router)
app.include_router(chat_ai.router)


@app.get("/", tags=["System"])
async def root():
    """Root landing endpoint with system status and documentation link."""
    return {
        "service": "Distress Monitoring ML Pipeline",
        "status": "online",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": [
            "POST /analyze/text",
            "POST /analyze/voice",
            "POST /score/distress",
            "POST /explain/distress",
            "POST /predict/escalation"
        ]
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Readiness check — reports whether each model subsystem is loaded."""
    return {
        "status": "ok",
        "text_analyzer_loaded": text_analyzer.is_loaded,
        "voice_analyzer_loaded": voice_analyzer.is_loaded,
        "escalation_predictor_loaded": escalation_predictor.is_loaded,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)

