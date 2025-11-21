"""Middleware для проверки доступа пользователей"""
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Any, Callable, Dict, Awaitable
from database import async_session_maker, UserRepository


class AuthMiddleware(BaseMiddleware):
    """Проверяет доступ пользователей к боту на основе БД"""
    
    async def __call__(
        self, 
        adviser: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], 
        event: TelegramObject, 
        data: Dict[str, Any]
    ) -> Any:

        user = getattr(event, "from_user", None)
        if not user:
            return await adviser(event, data)

        # Создаём async сессию для handler
        async with async_session_maker() as session:
            user_repo = UserRepository(session)
            db_user = await user_repo.get_or_create_by_telegram_id(
                telegram_id=user.id,
                username=user.username,
                full_name=user.full_name or f"{user.first_name} {user.last_name or ''}".strip()
            )

            # Обновляем last_seen
            await user_repo.update_last_seen(db_user)
            
            # Передаём данные пользователя (не ORM объект) в handler
            data['db_user'] = db_user
            data['session'] = session
            
            # Вызываем handler внутри контекста сессии
            return await adviser(event, data)
