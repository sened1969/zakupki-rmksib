"""Утилиты для обработки ошибок с понятными сообщениями"""
from typing import Optional
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)


ERROR_MESSAGES = {
    "database": {
        "title": "❌ Ошибка базы данных",
        "message": "Произошла ошибка при работе с базой данных.\n\n"
                   "Попробуйте позже или обратитесь к администратору.",
        "solutions": [
            "Проверьте подключение к базе данных",
            "Убедитесь, что все миграции применены",
            "Попробуйте повторить операцию позже"
        ]
    },
    "api": {
        "title": "❌ Ошибка API",
        "message": "Сервис временно недоступен.\n\n"
                   "Попробуйте позже.",
        "solutions": [
            "Проверьте подключение к интернету",
            "Убедитесь, что API ключи настроены правильно",
            "Попробуйте повторить операцию позже"
        ]
    },
    "file": {
        "title": "❌ Ошибка обработки файла",
        "message": "Не удалось обработать файл.\n\n"
                   "Проверьте формат и размер файла.",
        "solutions": [
            "Убедитесь, что файл в поддерживаемом формате",
            "Проверьте размер файла (максимум 20 МБ)",
            "Попробуйте загрузить файл заново"
        ]
    },
    "permission": {
        "title": "❌ Недостаточно прав",
        "message": "У вас нет прав для выполнения этого действия.",
        "solutions": [
            "Обратитесь к администратору для получения прав",
            "Проверьте свою роль в системе"
        ]
    },
    "validation": {
        "title": "❌ Ошибка валидации",
        "message": "Введенные данные некорректны.\n\n"
                   "Проверьте правильность ввода.",
        "solutions": [
            "Проверьте формат введенных данных",
            "Убедитесь, что все обязательные поля заполнены",
            "Попробуйте ввести данные заново"
        ]
    },
    "timeout": {
        "title": "⏱️ Превышено время ожидания",
        "message": "Операция заняла слишком много времени.\n\n"
                   "Попробуйте позже или упростите запрос.",
        "solutions": [
            "Попробуйте повторить операцию",
            "Упростите запрос (меньше данных)",
            "Проверьте подключение к интернету"
        ]
    },
    "unknown": {
        "title": "❌ Произошла ошибка",
        "message": "Произошла непредвиденная ошибка.\n\n"
                   "Мы уже работаем над её устранением.",
        "solutions": [
            "Попробуйте повторить операцию",
            "Обратитесь к администратору, если проблема повторяется"
        ]
    }
}


def get_error_message(
    error_type: str,
    custom_message: Optional[str] = None,
    show_solutions: bool = True
) -> str:
    """
    Получает понятное сообщение об ошибке
    
    Args:
        error_type: Тип ошибки (database, api, file, permission, validation, timeout, unknown)
        custom_message: Кастомное сообщение (опционально)
        show_solutions: Показывать ли решения
    
    Returns:
        Отформатированное сообщение об ошибке
    """
    error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["unknown"])
    
    text = f"<b>{error_info['title']}</b>\n\n"
    
    if custom_message:
        text += f"{custom_message}\n\n"
    else:
        text += f"{error_info['message']}\n\n"
    
    if show_solutions and error_info.get("solutions"):
        text += "<b>Что можно сделать:</b>\n"
        for i, solution in enumerate(error_info["solutions"], 1):
            text += f"{i}. {solution}\n"
    
    return text


async def handle_error(
    message: Message,
    error: Exception,
    error_type: str = "unknown",
    context: str = "",
    log_error: bool = True
) -> None:
    """
    Унифицированная обработка ошибок с отправкой понятного сообщения пользователю
    
    Args:
        message: Сообщение для отправки ошибки
        error: Исключение
        error_type: Тип ошибки
        context: Контекст ошибки (для логирования)
        log_error: Логировать ли ошибку
    """
    if log_error:
        logger.error(f"Error in {context}: {error}", exc_info=True)
    
    # Определяем тип ошибки по содержимому
    error_msg = str(error).lower()
    
    if "database" in error_msg or "connection" in error_msg or "sql" in error_msg:
        error_type = "database"
    elif "api" in error_msg or "http" in error_msg or "timeout" in error_msg:
        error_type = "api"
    elif "file" in error_msg or "document" in error_msg:
        error_type = "file"
    elif "permission" in error_msg or "access" in error_msg or "forbidden" in error_msg:
        error_type = "permission"
    elif "validation" in error_msg or "invalid" in error_msg:
        error_type = "validation"
    elif "timeout" in error_msg:
        error_type = "timeout"
    
    user_message = get_error_message(error_type, show_solutions=True)
    
    await message.answer(user_message, parse_mode="HTML")


def format_error_details(error: Exception) -> str:
    """
    Форматирует детали ошибки для отображения (только для админов)
    
    Args:
        error: Исключение
    
    Returns:
        Отформатированная строка с деталями ошибки
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    text = f"<b>Детали ошибки (для администратора):</b>\n\n"
    text += f"<b>Тип:</b> <code>{error_type}</code>\n"
    text += f"<b>Сообщение:</b> <code>{error_msg}</code>\n"
    
    return text

