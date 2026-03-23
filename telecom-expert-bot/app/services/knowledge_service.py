from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.knowledge import KnowledgeItem, KnowledgeCreate, KnowledgeUpdate, KnowledgeState
from app.models.user import User, UserRole


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_knowledge(self, data: KnowledgeCreate, user: User) -> KnowledgeItem:
        state = KnowledgeState.confirmed if user.role == UserRole.master else KnowledgeState.pending
        item = KnowledgeItem(
            title=data.title,
            content=data.content,
            domain=data.domain,
            feature=data.feature,
            spec_references=data.spec_references,
            state=state,
            created_by=user.id,
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def list_knowledge(
        self, state: Optional[KnowledgeState] = None, domain: Optional[str] = None
    ) -> List[KnowledgeItem]:
        query = select(KnowledgeItem)
        if state:
            query = query.where(KnowledgeItem.state == state)
        if domain:
            query = query.where(KnowledgeItem.domain == domain)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_knowledge(self, item_id: int) -> KnowledgeItem:
        result = await self.db.execute(
            select(KnowledgeItem).where(KnowledgeItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
        return item

    async def update_knowledge(self, item_id: int, data: KnowledgeUpdate, user: User) -> KnowledgeItem:
        item = await self.get_knowledge(item_id)
        if user.role != UserRole.master and item.created_by != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(item, field, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete_knowledge(self, item_id: int, user: User) -> bool:
        if user.role != UserRole.master:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Master role required")
        item = await self.get_knowledge(item_id)
        await self.db.delete(item)
        await self.db.flush()
        return True

    async def approve_knowledge(self, item_id: int, user: User) -> KnowledgeItem:
        if user.role != UserRole.master:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Master role required")
        item = await self.get_knowledge(item_id)
        item.state = KnowledgeState.confirmed
        item.approved_by = user.id
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def reject_knowledge(self, item_id: int, user: User) -> KnowledgeItem:
        if user.role != UserRole.master:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Master role required")
        item = await self.get_knowledge(item_id)
        item.state = KnowledgeState.rejected
        item.approved_by = user.id
        await self.db.flush()
        await self.db.refresh(item)
        return item
