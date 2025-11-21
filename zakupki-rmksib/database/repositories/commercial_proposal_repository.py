"""Репозиторий для работы с коммерческими предложениями"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from database.models import CommercialProposal


class CommercialProposalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> CommercialProposal:
        """Создать новое коммерческое предложение"""
        proposal = CommercialProposal(**kwargs)
        self.session.add(proposal)
        await self.session.commit()
        await self.session.refresh(proposal)
        return proposal

    async def get_by_id(self, proposal_id: int) -> Optional[CommercialProposal]:
        """Получить КП по ID"""
        result = await self.session.execute(select(CommercialProposal).where(CommercialProposal.id == proposal_id))
        return result.scalar_one_or_none()

    async def get_all(self, user_id: Optional[int] = None, limit: int = 100) -> List[CommercialProposal]:
        """Получить все КП (опционально фильтр по пользователю)"""
        query = select(CommercialProposal)
        if user_id:
            query = query.where(CommercialProposal.created_by == user_id)
        query = query.order_by(CommercialProposal.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_lot_id(self, lot_id: int) -> List[CommercialProposal]:
        """Получить все КП для конкретного лота"""
        result = await self.session.execute(
            select(CommercialProposal)
            .where(CommercialProposal.lot_id == lot_id)
            .order_by(CommercialProposal.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_unanalyzed(self, limit: int = 50) -> List[CommercialProposal]:
        """Получить КП, которые еще не были проанализированы"""
        result = await self.session.execute(
            select(CommercialProposal)
            .where(CommercialProposal.supplier_rating.is_(None))
            .order_by(CommercialProposal.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, proposal: CommercialProposal) -> CommercialProposal:
        """Обновить КП"""
        self.session.add(proposal)
        await self.session.commit()
        await self.session.refresh(proposal)
        return proposal

    async def delete(self, proposal: CommercialProposal) -> None:
        """Удалить КП"""
        await self.session.delete(proposal)
        await self.session.commit()
    
    async def delete_all_by_user(self, user_id: int) -> int:
        """Удалить все КП пользователя"""
        result = await self.session.execute(
            select(CommercialProposal).where(CommercialProposal.created_by == user_id)
        )
        proposals = list(result.scalars().all())
        count = len(proposals)
        for proposal in proposals:
            await self.session.delete(proposal)
        await self.session.commit()
        return count

