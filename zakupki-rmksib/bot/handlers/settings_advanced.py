"""Расширенные обработчики настроек (email, бюджет)"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.models import User
from database import async_session_maker, UserRepository, UserPreferenceRepository
from bot.keyboards.inline import (
    get_email_setup_menu,
    get_smtp_provider_menu,
    get_preferences_menu
)
from bot.states.forms import PreferenceStates
from utils.encryption import encrypt_password
from services.email.manager_email import ManagerEmailService
from loguru import logger

router = Router()


@router.callback_query(F.data == "pref:email")
async def email_setup_menu(callback: CallbackQuery, db_user: User):
    """Меню настройки email"""
    async with async_session_maker() as session:
        pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
        user = await UserRepository(session).get_by_telegram_id(db_user.telegram_id)
    
    email = user.contact_email if user else None
    smtp_provider = pref.smtp_provider or "не выбран"
    has_password = "✅" if pref.email_password else "❌"
    
    text = (
        f"📧 <b>Настройка Email</b>\n\n"
        f"📮 Email: {email or 'не указан'}\n"
        f"🔑 Пароль: {has_password} {'установлен' if pref.email_password else 'не установлен'}\n"
        f"📧 Провайдер: {smtp_provider}\n\n"
        f"Настройте параметры для отправки запросов КП поставщикам."
    )
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_email_setup_menu())
    await callback.answer()


@router.callback_query(F.data == "email:set_email")
async def start_email_input(callback: CallbackQuery, state: FSMContext):
    """Начало ввода email"""
    await state.set_state(PreferenceStates.email_input)
    await callback.message.edit_text(
        "✏️ <b>Введите email адрес:</b>\n\n"
        "Отправьте ваш email адрес для отправки запросов КП.\n"
        "Например: manager@example.com",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PreferenceStates.email_input)
async def process_email_input(message: Message, state: FSMContext, db_user: User):
    """Обработка введенного email"""
    email = message.text.strip()
    
    # Простая валидация email
    if "@" not in email or "." not in email.split("@")[1]:
        await message.answer("❌ Неверный формат email. Попробуйте снова.")
        return
    
    async with async_session_maker() as session:
        u_repo = UserRepository(session)
        user = await u_repo.get_by_telegram_id(db_user.telegram_id)
        if user:
            user.contact_email = email
            await u_repo.update(user)
    
    await message.answer(f"✅ Email сохранен: {email}")
    await state.clear()


@router.callback_query(F.data == "email:set_password")
async def start_password_input(callback: CallbackQuery, state: FSMContext):
    """Начало ввода пароля приложения"""
    await state.set_state(PreferenceStates.email_password_input)
    await callback.message.edit_text(
        "🔑 <b>Введите пароль приложения:</b>\n\n"
        "⚠️ <b>ВАЖНО:</b> Используйте пароль приложения, а не основной пароль!\n\n"
        "• <b>Yandex:</b> Создайте пароль приложения в настройках аккаунта\n"
        "• <b>Gmail:</b> Используйте пароль приложения из настроек безопасности\n"
        "• <b>Mail.ru:</b> Создайте пароль для внешних приложений\n\n"
        "Пароль будет зашифрован и сохранен в БД.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PreferenceStates.email_password_input)
async def process_password_input(message: Message, state: FSMContext, db_user: User):
    """Обработка введенного пароля"""
    password = message.text.strip()
    
    if len(password) < 8:
        await message.answer("❌ Пароль слишком короткий. Минимум 8 символов.")
        return
    
    try:
        # Шифруем пароль
        encrypted_password = encrypt_password(password)
        
        async with async_session_maker() as session:
            pref_repo = UserPreferenceRepository(session)
            pref = await pref_repo.get_or_create(db_user.id)
            await pref_repo.update_email_settings(pref, email_password=encrypted_password)
        
        await message.answer("✅ Пароль сохранен и зашифрован.")
        await state.clear()
    except Exception as e:
        logger.error(f"Error encrypting password: {e}")
        await message.answer("❌ Ошибка при сохранении пароля. Попробуйте снова.")


@router.callback_query(F.data == "email:set_provider")
async def smtp_provider_menu(callback: CallbackQuery):
    """Меню выбора SMTP провайдера"""
    await callback.message.edit_text(
        "📮 <b>Выберите почтовый провайдер:</b>\n\n"
        "Выберите сервис, который вы используете для email.",
        parse_mode="HTML",
        reply_markup=get_smtp_provider_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("smtp:"))
async def set_smtp_provider(callback: CallbackQuery, db_user: User):
    """Установка SMTP провайдера"""
    provider = callback.data.split(":")[1]  # yandex, gmail, mailru
    
    async with async_session_maker() as session:
        pref_repo = UserPreferenceRepository(session)
        pref = await pref_repo.get_or_create(db_user.id)
        await pref_repo.update_email_settings(pref, smtp_provider=provider)
    
    provider_names = {
        "yandex": "Yandex",
        "gmail": "Gmail",
        "mailru": "Mail.ru"
    }
    
    await callback.message.edit_text(
        f"✅ Провайдер установлен: <b>{provider_names.get(provider, provider)}</b>",
        parse_mode="HTML",
        reply_markup=get_email_setup_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "email:test")
async def test_email_connection(callback: CallbackQuery, db_user: User):
    """Тестирование подключения к email"""
    await callback.message.edit_text("🧪 Проверяю подключение к email...")
    
    async with async_session_maker() as session:
        pref_repo = UserPreferenceRepository(session)
        pref = await pref_repo.get_or_create(db_user.id)
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(db_user.telegram_id)
    
    if not user or not user.contact_email:
        await callback.message.edit_text(
            "❌ Email адрес не указан. Сначала укажите email.",
            reply_markup=get_email_setup_menu()
        )
        await callback.answer()
        return
    
    if not pref.email_password:
        await callback.message.edit_text(
            "❌ Пароль не установлен. Сначала укажите пароль приложения.",
            reply_markup=get_email_setup_menu()
        )
        await callback.answer()
        return
    
    if not pref.smtp_provider:
        await callback.message.edit_text(
            "❌ Провайдер не выбран. Сначала выберите SMTP провайдера.",
            reply_markup=get_email_setup_menu()
        )
        await callback.answer()
        return
    
    try:
        email_service = ManagerEmailService(
            email=user.contact_email,
            password=pref.email_password,
            smtp_provider=pref.smtp_provider
        )
        
        success, message = await email_service.test_connection()
        
        if success:
            await callback.message.edit_text(
                f"✅ <b>Подключение успешно!</b>\n\n{message}",
                parse_mode="HTML",
                reply_markup=get_email_setup_menu()
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Ошибка подключения:</b>\n\n{message}",
                parse_mode="HTML",
                reply_markup=get_email_setup_menu()
            )
    except Exception as e:
        logger.error(f"Error testing email connection: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ <b>Ошибка:</b>\n\n{str(e)}",
            parse_mode="HTML",
            reply_markup=get_email_setup_menu()
        )
    
    await callback.answer()


@router.callback_query(F.data == "pref:budget")
async def budget_setup_menu(callback: CallbackQuery, db_user: User):
    """Меню настройки бюджета"""
    async with async_session_maker() as session:
        pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
    
    budget_min = pref.budget_min or "не установлен"
    budget_max = pref.budget_max or "не установлен"
    
    text = (
        f"💰 <b>Настройка бюджета закупки</b>\n\n"
        f"От: {budget_min if isinstance(budget_min, str) else f'{budget_min:,} ₽'}\n"
        f"До: {budget_max if isinstance(budget_max, str) else f'{budget_max:,} ₽'}\n\n"
        f"Укажите диапазон бюджета для фильтрации лотов."
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = [
        [InlineKeyboardButton(text="✏️ Установить 'От'", callback_data="budget:set_min")],
        [InlineKeyboardButton(text="✏️ Установить 'До'", callback_data="budget:set_max")],
        [InlineKeyboardButton(text="🗑 Очистить", callback_data="budget:clear")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="pref:back")]
    ]
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "budget:set_min")
async def start_budget_min_input(callback: CallbackQuery, state: FSMContext):
    """Начало ввода минимального бюджета"""
    await state.set_state(PreferenceStates.budget_min_input)
    await callback.message.edit_text(
        "💰 <b>Введите минимальную сумму бюджета (в рублях):</b>\n\n"
        "Например: 100000\n"
        "Или отправьте 0 для сброса.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PreferenceStates.budget_min_input)
async def process_budget_min(message: Message, state: FSMContext, db_user: User):
    """Обработка минимального бюджета"""
    try:
        value = int(message.text.strip())
        if value < 0:
            await message.answer("❌ Сумма не может быть отрицательной.")
            return
        
        async with async_session_maker() as session:
            pref_repo = UserPreferenceRepository(session)
            pref = await pref_repo.get_or_create(db_user.id)
            await pref_repo.update_budget(pref, budget_min=value if value > 0 else None)
        
        await message.answer(f"✅ Минимальный бюджет установлен: {value:,} ₽" if value > 0 else "✅ Минимальный бюджет сброшен")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число. Например: 100000")


@router.callback_query(F.data == "budget:set_max")
async def start_budget_max_input(callback: CallbackQuery, state: FSMContext):
    """Начало ввода максимального бюджета"""
    await state.set_state(PreferenceStates.budget_max_input)
    await callback.message.edit_text(
        "💰 <b>Введите максимальную сумму бюджета (в рублях):</b>\n\n"
        "Например: 5000000\n"
        "Или отправьте 0 для сброса.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PreferenceStates.budget_max_input)
async def process_budget_max(message: Message, state: FSMContext, db_user: User):
    """Обработка максимального бюджета"""
    try:
        value = int(message.text.strip())
        if value < 0:
            await message.answer("❌ Сумма не может быть отрицательной.")
            return
        
        async with async_session_maker() as session:
            pref_repo = UserPreferenceRepository(session)
            pref = await pref_repo.get_or_create(db_user.id)
            
            # Проверяем, что max >= min
            if pref.budget_min and value > 0 and value < pref.budget_min:
                await message.answer(
                    f"❌ Максимальная сумма ({value:,} ₽) не может быть меньше минимальной ({pref.budget_min:,} ₽)."
                )
                return
            
            await pref_repo.update_budget(pref, budget_max=value if value > 0 else None)
        
        await message.answer(f"✅ Максимальный бюджет установлен: {value:,} ₽" if value > 0 else "✅ Максимальный бюджет сброшен")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число. Например: 5000000")


@router.callback_query(F.data == "budget:clear")
async def clear_budget(callback: CallbackQuery, db_user: User):
    """Очистка настроек бюджета"""
    async with async_session_maker() as session:
        pref_repo = UserPreferenceRepository(session)
        pref = await pref_repo.get_or_create(db_user.id)
        await pref_repo.update_budget(pref, budget_min=None, budget_max=None)
    
    await callback.message.edit_text("✅ Настройки бюджета очищены.")
    await callback.answer()












