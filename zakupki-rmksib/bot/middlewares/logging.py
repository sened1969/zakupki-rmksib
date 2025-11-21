from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Any, Callable, Dict, Awaitable
from loguru import logger

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], event: Message | CallbackQuery, data: Dict[str, Any]) -> Any:
        logger.info(f"Update from user {getattr(getattr(event, 'from_user', None), 'id', 'unknown')} | type={type(event).__name__}")
        return await handler(event, data)
