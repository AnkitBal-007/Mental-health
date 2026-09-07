"""SQLAlchemy model for Users."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="district")  # district, state, national, counsellor
    district = Column(String(100), nullable=True, index=True)      # e.g., "Patna", "Lucknow", "Bhopal"
    state = Column(String(100), nullable=True, index=True)            # e.g., "Bihar", "Uttar Pradesh"
    full_name = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
