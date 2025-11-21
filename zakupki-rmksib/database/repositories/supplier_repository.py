"""Репозиторий для работы с поставщиками"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from database.models import Supplier


class SupplierRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Supplier:
        """Создать нового поставщика"""
        supplier = Supplier(**kwargs)
        self.session.add(supplier)
        await self.session.commit()
        await self.session.refresh(supplier)
        return supplier

    async def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        """Получить поставщика по ID"""
        result = await self.session.execute(select(Supplier).where(Supplier.id == supplier_id))
        return result.scalar_one_or_none()

    async def get_by_inn(self, inn: str) -> Optional[Supplier]:
        """Получить поставщика по ИНН"""
        result = await self.session.execute(select(Supplier).where(Supplier.inn == inn))
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100) -> List[Supplier]:
        """Получить всех поставщиков"""
        result = await self.session.execute(
            select(Supplier).order_by(Supplier.reliability_rating.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def search_by_name(self, name_part: str, limit: int = 50) -> List[Supplier]:
        """Поиск поставщиков по части названия"""
        result = await self.session.execute(
            select(Supplier)
            .where(Supplier.name.ilike(f"%{name_part}%"))
            .order_by(Supplier.reliability_rating.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, supplier: Supplier) -> Supplier:
        """Обновить поставщика"""
        self.session.add(supplier)
        await self.session.commit()
        await self.session.refresh(supplier)
        return supplier

    async def delete(self, supplier: Supplier) -> None:
        """Удалить поставщика"""
        await self.session.delete(supplier)
        await self.session.commit()



















