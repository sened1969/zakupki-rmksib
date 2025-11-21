from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from bot.keyboards.reply import get_main_menu, get_start_keyboard
from database.models import User


router = Router()


@router.message(CommandStart())
async def start(message: Message, db_user: User = None) -> None:
    """Обработчик команды /start"""
    # Используем только те атрибуты, что есть в User модели
    name = message.from_user.full_name or "Пользователь"
    
    await message.answer(
        f"Здравствуйте, {name}!\n\n"
        f"Я AI-ассистент закупок РМКСИБ.\n\n"
        f"Выберите действие в меню ниже.",
        reply_markup=get_main_menu(is_admin=db_user.role == "admin" if db_user else False),
    )


@router.message(F.text == "🚀 Старт")
async def start_button_handler(message: Message, db_user: User = None) -> None:
    """Обработчик кнопки Старт"""
    # Используем только те атрибуты, что есть в User модели
    name = message.from_user.full_name or "Пользователь"
    
    await message.answer(
        f"Здравствуйте, {name}!\n\n"
        f"Я AI-ассистент закупок РМКСИБ.\n\n"
        f"Выберите действие в меню ниже.",
        reply_markup=get_main_menu(is_admin=db_user.role == "admin" if db_user else False),
    )


@router.message(Command("help"))
async def help_cmd(message: Message, db_user: User = None) -> None:
    await message.answer(
        "Доступные команды: /start, /help",
        reply_markup=get_main_menu(is_admin=db_user.role == "admin" if db_user else False)
    )


@router.callback_query(F.data == "menu:main")
async def back_to_main_menu(callback: CallbackQuery, db_user: User = None) -> None:
    """Обработчик кнопки 'Главное меню'"""
    await callback.answer()
    name = callback.from_user.full_name or "Пользователь"
    
    try:
        await callback.message.edit_text(
            f"🏠 <b>Главное меню</b>\n\n"
            f"Здравствуйте, {name}!\n\n"
            f"Выберите действие в меню ниже.",
            parse_mode="HTML"
        )
    except Exception:
        # Если не удалось отредактировать, отправляем новое сообщение
        await callback.message.answer(
            f"🏠 <b>Главное меню</b>\n\n"
            f"Здравствуйте, {name}!\n\n"
            f"Выберите действие в меню ниже.",
            parse_mode="HTML",
            reply_markup=get_main_menu(is_admin=db_user.role == "admin" if db_user else False)
        )



