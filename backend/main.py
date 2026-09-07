"""
Backend Service — Victim Distress-Monitoring & Case Management System
=====================================================================

FastAPI backend providing:
  - Anonymized victim record management & jurisdictional RBAC
  - Cross-channel check-in tracking (Chatbot, IVRS, SMS, Portal)
  - Proactive ML-driven alert evaluation & threshold monitoring
  - Evidence-backed intervention recommendation engine
  - Role-scoped dashboards (District / State / National / Counsellor)

Service port: 8000 (configurable via BACKEND_PORT env var)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from config import HOST, PORT, ALLOWED_ORIGINS
from database import engine, Base, SessionLocal
from models.user import User
from routers import auth, victims, check_ins, alerts, dashboard, admin
from seed_data import seed_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Automatic database schema initialization on startup.
    Creates all tables (victims, check_ins, alerts, users, audit_logs) via SQLAlchemy.
    Automatically seeds initial demo accounts if database is empty.
    """
    logger.info("Initializing database schema for cloud deployment...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")

        # Check if database has users; if empty, automatically seed demo records
        db = SessionLocal()
        try:
            if db.query(User).count() == 0:
                logger.info("Empty database detected — auto-seeding demo users and initial records...")
                seed_database()
                logger.info("Auto-seeding complete.")
        finally:
            db.close()

    except Exception as e:
        logger.error("Database schema initialization error: %s", e)

    yield
    logger.info("Backend service shutting down.")


app = FastAPI(
    title="Distress Monitoring Case Management Backend",
    description=(
        "Backend API for the SIH AI-Powered Mental Health Distress Monitoring System.\n\n"
        "**Core Capabilities:**\n"
        "- Anonymized Victim Registry (SC/ST Act, Atrocity cases, Witness Intimidation)\n"
        "- Multi-Channel Check-in Tracking\n"
        "- ML Pipeline Integration (Distress Scoring, SHAP Explainability & Escalation Forecasting)\n"
        "- Role-based Access Control (District / State / National / Counsellor)\n"
        "- Automated Risk Alerts & Interventions\n"
        "- Audit Logging & Compliance Protection"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow configured origins and all Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth.router)
app.include_router(victims.router)
app.include_router(check_ins.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/", tags=["System"])
def root_endpoint():
    """Service status and quick links."""
    return {
        "service": "Victim Distress Monitoring Backend API",
        "status": "online",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
def health_check():
    """Readiness probe for cloud hosting platforms (Render, Railway, Kubernetes)."""
    return {"status": "ok", "service": "backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
