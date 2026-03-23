from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query import QueryRequest, QueryResponse
from app.services.llm_service import LLMService
from app.services.spec_retriever import SpecRetriever
from app.utils.auth import require_child_or_master_role
from app.utils.reference_mapper import detect_domain_from_query
from app.db.database import get_db
from app.config import settings

router = APIRouter(prefix="/query", tags=["query"])

llm_service = LLMService()
spec_retriever = SpecRetriever(
    persist_directory=settings.chroma_persist_directory,
    collection_name=settings.chroma_collection_name,
)


@router.post("", response_model=dict)
async def process_query(
    request: QueryRequest,
    current_user=Depends(require_child_or_master_role),
    db: AsyncSession = Depends(get_db),
):
    domain = request.domain or detect_domain_from_query(request.question)
    context = await spec_retriever.get_context_for_query(request.question)
    if request.context:
        context = f"{request.context}\n\n{context}" if context else request.context

    result = await llm_service.query(request.question, context=context or None)

    response = QueryResponse(
        answer=result["answer"],
        references=result.get("references", []),
        domain=result.get("domain") or domain,
        message_flow=result.get("message_flow"),
        edge_cases=result.get("edge_cases"),
        confidence=result.get("confidence", "medium"),
        sources=[],
    )

    return {
        "status": "success",
        "data": response.model_dump(),
        "message": "Query processed successfully",
    }
