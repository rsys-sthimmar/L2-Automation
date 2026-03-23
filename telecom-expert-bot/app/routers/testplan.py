from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query import TestPlanRequest, TestPlanResponse
from app.services.testplan_generator import TestPlanGenerator
from app.services.llm_service import LLMService
from app.utils.auth import require_child_or_master_role
from app.db.database import get_db

router = APIRouter(prefix="/testplan", tags=["testplan"])

test_plan_generator = TestPlanGenerator()
llm_service = LLMService()


@router.post("/generate", response_model=dict)
async def generate_test_plan(
    request: TestPlanRequest,
    current_user=Depends(require_child_or_master_role),
    db: AsyncSession = Depends(get_db),
):
    result = await test_plan_generator.generate(
        feature=request.feature,
        domain=request.domain,
        requirements=request.requirements,
        llm_service=llm_service,
    )
    response = TestPlanResponse(**result)
    return {
        "status": "success",
        "data": response.model_dump(),
        "message": "Test plan generated successfully",
    }
