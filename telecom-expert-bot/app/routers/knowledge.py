from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeCreate, KnowledgeUpdate, KnowledgeState
from app.services.knowledge_service import KnowledgeService
from app.utils.auth import require_child_or_master_role, require_master_role
from app.db.database import get_db

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("", response_model=dict)
async def create_knowledge(
    data: KnowledgeCreate,
    current_user=Depends(require_child_or_master_role),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    item = await service.create_knowledge(data, current_user)
    return {"status": "success", "data": _serialize(item), "message": "Knowledge item created"}


@router.get("", response_model=dict)
async def list_knowledge(
    state: Optional[KnowledgeState] = Query(None),
    domain: Optional[str] = Query(None),
    current_user=Depends(require_child_or_master_role),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    items = await service.list_knowledge(state=state, domain=domain)
    return {"status": "success", "data": [_serialize(i) for i in items], "message": "OK"}


@router.get("/{item_id}", response_model=dict)
async def get_knowledge(
    item_id: int,
    current_user=Depends(require_child_or_master_role),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    item = await service.get_knowledge(item_id)
    return {"status": "success", "data": _serialize(item), "message": "OK"}


@router.put("/{item_id}", response_model=dict)
async def update_knowledge(
    item_id: int,
    data: KnowledgeUpdate,
    current_user=Depends(require_child_or_master_role),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    item = await service.update_knowledge(item_id, data, current_user)
    return {"status": "success", "data": _serialize(item), "message": "Knowledge item updated"}


@router.delete("/{item_id}", response_model=dict)
async def delete_knowledge(
    item_id: int,
    current_user=Depends(require_master_role),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    await service.delete_knowledge(item_id, current_user)
    return {"status": "success", "data": None, "message": "Knowledge item deleted"}


@router.post("/{item_id}/approve", response_model=dict)
async def approve_knowledge(
    item_id: int,
    current_user=Depends(require_master_role),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    item = await service.approve_knowledge(item_id, current_user)
    return {"status": "success", "data": _serialize(item), "message": "Knowledge item approved"}


@router.post("/{item_id}/reject", response_model=dict)
async def reject_knowledge(
    item_id: int,
    current_user=Depends(require_master_role),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    item = await service.reject_knowledge(item_id, current_user)
    return {"status": "success", "data": _serialize(item), "message": "Knowledge item rejected"}


def _serialize(item) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "domain": item.domain,
        "feature": item.feature,
        "spec_references": item.spec_references,
        "state": item.state.value if hasattr(item.state, 'value') else item.state,
        "created_by": item.created_by,
        "approved_by": item.approved_by,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }
