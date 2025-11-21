"""Утилиты для отображения индикаторов загрузки"""
from aiogram.types import Message
from typing import Optional


async def show_loading_indicator(message: Message, text: str = "⏳ Обработка...") -> Message:
    """
    Показывает индикатор загрузки
    
    Args:
        message: Сообщение для редактирования или отправки нового
        text: Текст индикатора загрузки
    
    Returns:
        Сообщение с индикатором загрузки
    """
    loading_text = f"⏳ <b>{text}</b>\n\n"
    loading_text += "Пожалуйста, подождите..."
    
    try:
        # Пытаемся отредактировать существующее сообщение
        await message.edit_text(loading_text, parse_mode="HTML")
        return message
    except Exception:
        # Если не получилось, отправляем новое сообщение
        return await message.answer(loading_text, parse_mode="HTML")


async def update_loading_message(
    message: Message,
    new_text: str,
    parse_mode: str = "HTML",
    reply_markup=None
) -> None:
    """
    Обновляет сообщение с индикатором загрузки на финальный результат
    
    Args:
        message: Сообщение для обновления
        new_text: Новый текст
        parse_mode: Режим парсинга
        reply_markup: Клавиатура (опционально)
    """
    try:
        await message.edit_text(new_text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception:
        # Если не получилось отредактировать, отправляем новое сообщение
        await message.answer(new_text, parse_mode=parse_mode, reply_markup=reply_markup)

