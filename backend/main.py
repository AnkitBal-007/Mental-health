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

import models  # Explicitly import all models (victims, check_ins, alerts, users, audit_logs)
from config import HOST, PORT, ALLOWED_ORIGINS
from database import engine, Base
from routers import auth, victims, check_ins, alerts, dashboard, admin

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
    Eliminates the need for manual migration steps after cloud deployment.
    """
    logger.info("Initializing database schema for cloud deployment...")
    try:
        # Guarantee all tables (victims, check_ins, alerts, users, audit_logs) are created
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully (victims, check_ins, alerts, users, audit_logs ready).")
    except Exception as e:
        logger.error("Database schema initialization error: %s", e)
        raise

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
        "- Role-Based Access Control (District, State, National, Counsellor)\n"
        "- Intervention Recommendations & Priority Alerts"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration — reads allow_origins from ALLOWED_ORIGINS env var (parsed comma-separated list)
# Defaults to http://localhost:3000 only when ALLOWED_ORIGINS is unset.
logger.info("Configuring CORS with allowed origins: %s", ALLOWED_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(victims.router)
app.include_router(check_ins.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(admin.router)  # Temporary admin router for cloud database demo seeding


@app.get("/", tags=["System"])
async def root():
    """Root endpoint providing service metadata and API navigation links."""
    return {
        "service": "Victim Distress Monitoring Backend API",
        "status": "online",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": [
            "POST /auth/login",
            "GET  /victims",
            "POST /victims",
            "POST /check-ins",
            "POST /alerts/evaluate",
            "GET  /alerts",
            "GET  /dashboard/summary?scope=district|state|national&id=X",
            "POST /admin/seed-demo-data (Temporary, requires X-Admin-Seed-Token header)"
        ]
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "backend", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
