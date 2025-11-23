"""Репозиторий для работы с лотами"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta
from database.models import Lot


class LotRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Lot:
        """Создать новый лот"""
        lot = Lot(**kwargs)
        self.session.add(lot)
        await self.session.commit()
        await self.session.refresh(lot)
        return lot

    async def get_by_id(self, lot_id: int) -> Optional[Lot]:
        """Получить лот по ID"""
        result = await self.session.execute(select(Lot).where(Lot.id == lot_id))
        return result.scalar_one_or_none()

    async def get_by_lot_number(self, lot_number: str) -> Optional[Lot]:
        """Получить лот по номеру"""
        result = await self.session.execute(select(Lot).where(Lot.lot_number == lot_number))
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, inverted: bool = False, exclude_expired: bool = True) -> List[Lot]:
        """
        Получить все лоты
        
        Args:
            limit: Максимальное количество лотов
            inverted: Сортировать по убыванию ID (новые первыми)
            exclude_expired: Исключить лоты с прошедшим дедлайном (по умолчанию True)
        """
        query = select(Lot)
        
        # Фильтруем лоты с прошедшим дедлайном
        if exclude_expired:
            query = query.where(Lot.deadline >= datetime.utcnow())
        
        if inverted:
            query = query.order_by(Lot.id.desc())
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, lot: Lot) -> Lot:
        """Обновить лот"""
        self.session.add(lot)
        await self.session.commit()
        await self.session.refresh(lot)
        return lot

    async def delete(self, lot: Lot) -> None:
        """Удалить лот"""
        await self.session.delete(lot)
        await self.session.commit()
    
    async def get_expired_lots(self, days_before_expiry: int = 0) -> List[Lot]:
        """
        Получить лоты с прошедшим дедлайном
        
        Args:
            days_before_expiry: По умолчанию 0 - возвращает только лоты с уже прошедшим дедлайном (deadline < now).
                              Если > 0, то возвращает лоты, у которых дедлайн прошел более X дней назад.
                              Например, days_before_expiry=1 вернет лоты с дедлайном < (сегодня - 1 день).
        
        Returns:
            Список лотов с прошедшим дедлайном
        """
        # Вычисляем дату истечения (сегодня - days_before_expiry дней)
        # Если days_before_expiry = 0, то expiry_date = сейчас, ищем лоты с deadline < сейчас (уже прошедшие)
        expiry_date = datetime.utcnow() - timedelta(days=days_before_expiry)
        
        # Ищем лоты, у которых deadline < expiry_date (уже прошедшие)
        query = select(Lot).where(Lot.deadline < expiry_date)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def delete_expired_lots(self, days_before_expiry: int = 0) -> int:
        """
        Удалить лоты с прошедшим дедлайном
        
        Args:
            days_before_expiry: По умолчанию 0 - удаляет только лоты с уже прошедшим дедлайном (deadline < now).
                              Если > 0, то удаляет лоты, у которых дедлайн прошел более X дней назад.
        
        Returns:
            Количество удаленных лотов
        """
        expired_lots = await self.get_expired_lots(days_before_expiry)
        count = len(expired_lots)
        
        for lot in expired_lots:
            await self.delete(lot)
        
        return count










