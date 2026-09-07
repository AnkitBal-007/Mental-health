"""
Database session management and base model definition using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Handle SQLite vs PostgreSQL specific connect args
connect_args = {}
engine_kwargs = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Cloud PostgreSQL (Supabase/RDS/Neon) connection resilience
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
except Exception as e:
    logger.error("Failed to initialize database engine for DATABASE_URL: %s", e)
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency to provide a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
