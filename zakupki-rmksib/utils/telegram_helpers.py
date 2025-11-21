"""Утилиты для работы с Telegram API"""
from typing import List
from aiogram.types import Message
from aiogram import Bot


async def send_long_message(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: str = "HTML",
    max_length: int = 4096,
    reply_markup=None
) -> List[Message]:
    """
    Отправляет длинное сообщение, разбивая его на части если необходимо
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        text: Текст сообщения
        parse_mode: Режим парсинга (HTML/Markdown)
        max_length: Максимальная длина одного сообщения (по умолчанию 4096 для Telegram)
        reply_markup: Клавиатура (будет добавлена только к последнему сообщению)
    
    Returns:
        Список отправленных сообщений
    """
    if bot is None:
        raise ValueError("Bot instance is required")
    
    messages = []
    
    if len(text) <= max_length:
        # Сообщение помещается в один раз
        msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        messages.append(msg)
        return messages
    
    # Разбиваем на части
    parts = []
    current_part = ""
    
    # Разбиваем по строкам для более аккуратного разбиения
    lines = text.split('\n')
    
    for line in lines:
        # Если добавление текущей строки не превысит лимит
        if len(current_part) + len(line) + 1 <= max_length:
            current_part += line + '\n'
        else:
            # Сохраняем текущую часть
            if current_part:
                parts.append(current_part.rstrip())
            
            # Если одна строка длиннее лимита, разбиваем её
            if len(line) > max_length:
                # Разбиваем длинную строку на куски
                words = line.split(' ')
                temp_line = ""
                for word in words:
                    if len(temp_line) + len(word) + 1 <= max_length:
                        temp_line += word + " "
                    else:
                        if temp_line:
                            parts.append(temp_line.rstrip())
                        temp_line = word + " "
                current_part = temp_line
            else:
                current_part = line + '\n'
    
    # Добавляем последнюю часть
    if current_part:
        parts.append(current_part.rstrip())
    
    # Отправляем все части
    for i, part in enumerate(parts):
        # Клавиатуру добавляем только к последнему сообщению
        markup = reply_markup if i == len(parts) - 1 else None
        
        msg = await bot.send_message(
            chat_id=chat_id,
            text=part,
            parse_mode=parse_mode,
            reply_markup=markup
        )
        messages.append(msg)
    
    return messages


def truncate_text(text: str, max_length: int = 4000, suffix: str = "...") -> str:
    """
    Обрезает текст до максимальной длины
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
    
    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

