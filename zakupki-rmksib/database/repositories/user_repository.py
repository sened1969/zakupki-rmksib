"""Репозиторий для работы с пользователями"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from database.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> User:
        """Создать нового пользователя"""
        user = User(**kwargs)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_or_create_by_telegram_id(self, telegram_id: int, username: str | None = None, full_name: str | None = None) -> User:
        """Получить существующего пользователя или создать нового"""
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self.create(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                role="user",
                is_active=True
            )
        else:
            # Обновляем username и last_seen при каждом входе
            if username or full_name:
                user.username = username
                user.full_name = full_name
                await self.update(user)
        return user

    async def get_all_active(self, limit: int = 100) -> List[User]:
        """Получить всех активных пользователей"""
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_role(self, role: str) -> List[User]:
        """Получить пользователей по роли"""
        result = await self.session.execute(
            select(User).where(User.role == role)
        )
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        """Обновить пользователя"""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def deactivate(self, user: User) -> User:
        """Деактивировать пользователя"""
        user.is_active = False
        return await self.update(user)

    async def activate(self, user: User) -> User:
        """Активировать пользователя"""
        user.is_active = True
        return await self.update(user)

    async def set_role(self, user: User, role: str) -> User:
        """Установить роль пользователю"""
        user.role = role
        return await self.update(user)

    async def update_last_seen(self, user: User) -> User:
        """Обновить время последнего визита"""
        from datetime import datetime
        user.last_seen = datetime.utcnow()
        return await self.update(user)



















