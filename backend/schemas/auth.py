"""Pydantic models for Authentication and Users."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Plaintext password")


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    role: str = Field(..., description="district, state, national, counsellor")
    district: Optional[str] = None
    state: Optional[str] = None
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    district: Optional[str] = None
    state: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    district: Optional[str] = None
    state: Optional[str] = None
    username: str


class TokenPayload(BaseModel):
    sub: str  # username
    user_id: int
    role: str
    district: Optional[str] = None
    state: Optional[str] = None
    exp: Optional[int] = None
