"""Reply keyboards"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_start_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой Старт для очищенного чата"""
    keyboard = [
        [KeyboardButton(text="🚀 Старт")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Основная клавиатура для пользователя"""
    keyboard = [
        [KeyboardButton(text="📋 Мои лоты"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="📄 Анализ КП"), KeyboardButton(text="🔍 Поиск Поставщиков")],
        [KeyboardButton(text="➕ Создать лот"), KeyboardButton(text="⚙️ Настройки")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="👑 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура админ-панели"""
    keyboard = [
        [KeyboardButton(text="Управление пользователями")],
        [KeyboardButton(text="Статистика системы")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
