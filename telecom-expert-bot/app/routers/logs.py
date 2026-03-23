from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query import LogAnalysisRequest, LogAnalysisResponse
from app.services.log_analyzer import LogAnalyzer
from app.services.llm_service import LLMService
from app.utils.auth import require_child_or_master_role
from app.db.database import get_db

router = APIRouter(prefix="/logs", tags=["logs"])

log_analyzer = LogAnalyzer()
llm_service = LLMService()


@router.post("/analyze", response_model=dict)
async def analyze_logs(
    request: LogAnalysisRequest,
    current_user=Depends(require_child_or_master_role),
    db: AsyncSession = Depends(get_db),
):
    result = await log_analyzer.analyze(request.log_text, llm_service=llm_service)
    response = LogAnalysisResponse(
        decoded_messages=result["decoded_messages"],
        failures=result["failures"],
        procedure_map=result["procedure_map"],
        root_cause=result["root_cause"],
        suggestions=result["suggestions"],
        confidence=result["confidence"],
        raw_analysis=result["raw_analysis"],
    )
    return {
        "status": "success",
        "data": response.model_dump(),
        "message": "Log analysis completed",
    }
