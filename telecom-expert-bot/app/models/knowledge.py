from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SAEnum
from pydantic import BaseModel, ConfigDict

from app.db.database import Base


class KnowledgeState(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    domain = Column(String(50), nullable=False)
    feature = Column(String(100), nullable=True)
    spec_references = Column(JSON, default=list)
    state = Column(SAEnum(KnowledgeState), default=KnowledgeState.pending, nullable=False)
    created_by = Column(Integer, nullable=False)
    approved_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class KnowledgeCreate(BaseModel):
    title: str
    content: str
    domain: str
    feature: Optional[str] = None
    spec_references: List[str] = []


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    domain: Optional[str] = None
    feature: Optional[str] = None
    spec_references: Optional[List[str]] = None


class KnowledgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    domain: str
    feature: Optional[str]
    spec_references: List[Any]
    state: KnowledgeState
    created_by: int
    approved_by: Optional[int]
    created_at: datetime
    updated_at: datetime
