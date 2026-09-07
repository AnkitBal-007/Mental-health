"""
Configuration settings for the Backend Service.

Fully cloud-ready configuration reading all secrets, database credentials,
CORS origins, and pipeline integrations from environment variables.
"""

import os
from typing import List

from dotenv import load_dotenv

# Load .env file from workspace root or backend dir
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── 1. Database Configuration ────────────────────────────────────────────────
# In production (Render/Railway/Supabase), DATABASE_URL must be provided.
# Automatically normalizes 'postgres://' to 'postgresql://' for SQLAlchemy.
_raw_database_url = os.getenv("DATABASE_URL", "").strip()

if _raw_database_url and not _raw_database_url.startswith("postgresql://mindguard_admin:REPLACE_WITH"):
    if _raw_database_url.startswith("postgres://"):
        _raw_database_url = _raw_database_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = _raw_database_url
else:
    # Only fallback to local SQLite when DATABASE_URL is not provided or is unconfigured placeholder (local dev)
    DATABASE_URL: str = "sqlite:///./distress_monitoring.db"

# ── 2. JWT & Authentication ──────────────────────────────────────────────────
# Reads JWT_SECRET (or JWT_SECRET_KEY). In production, a secure secret must be set.
_raw_jwt = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY") or ""
if not _raw_jwt or "REPLACE_WITH" in _raw_jwt:
    JWT_SECRET: str = "sih-distress-monitoring-secret-key-2024-secure-dev-fallback-key"
else:
    JWT_SECRET: str = _raw_jwt
JWT_SECRET_KEY: str = JWT_SECRET  # Backward compatibility alias
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# ── 3. CORS Allowed Origins ──────────────────────────────────────────────────
# Reads comma-separated list of allowed origins from ALLOWED_ORIGINS (or CORS_ORIGINS).
# By default in cloud/local environments, allows localhost and any vercel preview/production domain.
_origins_env = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS") or ""
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://saathiai-six.vercel.app",
]

if _origins_env.strip():
    ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _origins_env.split(",") if origin.strip()]
    for d in DEFAULT_ORIGINS:
        if d not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(d)
else:
    ALLOWED_ORIGINS: List[str] = DEFAULT_ORIGINS

# ── 4. Temporary Admin Seed Token ────────────────────────────────────────────
# Secret token required to trigger POST /admin/seed-demo-data
ADMIN_SEED_TOKEN: str = os.getenv("ADMIN_SEED_TOKEN", "").strip()

# ── 5. ML Pipeline Service Integration ───────────────────────────────────────
ML_PIPELINE_URL: str = os.getenv("ML_PIPELINE_URL", "http://localhost:8001")

# ── 6. Alert Thresholds ──────────────────────────────────────────────────────
DISTRESS_ALERT_THRESHOLD: float = float(os.getenv("DISTRESS_ALERT_THRESHOLD", "70.0"))
ESCALATION_PROB_THRESHOLD: float = float(os.getenv("ESCALATION_PROB_THRESHOLD", "0.60"))

# ── 7. Recommendation Rules JSON Config Path ─────────────────────────────────
RECOMMENDATION_RULES_PATH: str = os.getenv(
    "RECOMMENDATION_RULES_PATH",
    os.path.join(os.path.dirname(__file__), "config", "recommendation_rules.json")
)

# ── 8. Server Host & Port ────────────────────────────────────────────────────
HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT") or os.getenv("BACKEND_PORT") or "8000")

# Supported user roles
USER_ROLES: List[str] = ["district", "state", "national", "counsellor"]
