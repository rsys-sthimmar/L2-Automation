from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from pydantic import BaseModel, ConfigDict

from app.db.database import Base


class UserRole(str, Enum):
    master = "master"
    child = "child"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.child, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.child


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str
