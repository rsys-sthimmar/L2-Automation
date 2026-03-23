from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    domain: Optional[str] = None
    context: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    references: List[str] = []
    domain: Optional[str] = None
    message_flow: Optional[str] = None
    edge_cases: Optional[List[str]] = None
    confidence: ConfidenceLevel = ConfidenceLevel.medium
    sources: List[Dict[str, Any]] = []


class LogAnalysisRequest(BaseModel):
    log_text: str = Field(..., min_length=1)
    context: Optional[str] = None


class LogAnalysisResponse(BaseModel):
    decoded_messages: List[Dict[str, Any]] = []
    failures: List[str] = []
    procedure_map: Optional[str] = None
    root_cause: Optional[str] = None
    suggestions: List[str] = []
    confidence: ConfidenceLevel = ConfidenceLevel.medium
    raw_analysis: Optional[str] = None


class TestPlanRequest(BaseModel):
    feature: str = Field(..., min_length=1)
    domain: str
    requirements: Optional[List[str]] = None
    context: Optional[str] = None


class TestPlanResponse(BaseModel):
    objective: str
    preconditions: List[str] = []
    steps: List[Dict[str, Any]] = []
    expected_results: List[str] = []
    negative_scenarios: List[Dict[str, Any]] = []
    kpis: List[str] = []
    references: List[str] = []
