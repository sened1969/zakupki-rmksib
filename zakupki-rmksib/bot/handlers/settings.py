"""Обработчики для настроек"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.models import User
from database import async_session_maker, UserRepository, UserPreferenceRepository
from bot.keyboards.inline import get_preferences_menu, get_customer_selection, get_nomenclature_selection, get_notify_toggle
from bot.states.forms import PreferenceStates

router = Router()


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message, db_user: User) -> None:
    """Показать настройки пользователя"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Settings button pressed by user {db_user.telegram_id}, text: '{message.text}', text bytes: {message.text.encode('utf-8')}")
    
    try:
        async with async_session_maker() as session:
            pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
        
        text = "⚙️ <b>Ваши настройки</b>\n\n"
        text += "👤 <b>Профиль:</b>\n"
        text += f"  Имя: {db_user.full_name or 'Не указано'}\n"
        text += f"  Email: {db_user.contact_email or 'Не указан'}\n"
        text += f"  Роль: {'👑 Администратор' if db_user.role == 'admin' else '👤 Менеджер' if db_user.role == 'manager' else '👤 Пользователь'}\n\n"
        text += "🔔 <b>Уведомления:</b>\n"
        text += f"  Статус: {'✅ Включены' if pref.notify_enabled else '❌ Выключены'}\n"
        text += f"  Заказчики: {', '.join(pref.customers or []) or 'все'}\n"
        text += f"  Номенклатура: {', '.join(pref.nomenclature or []) or 'вся'}\n"
        text += f"  Бюджет: {f'{pref.budget_min:,} - {pref.budget_max:,} ₽' if pref.budget_min and pref.budget_max else 'не установлен'}\n\n"
        text += "📧 <b>Email для рассылки КП:</b>\n"
        text += f"  Провайдер: {pref.smtp_provider or 'не выбран'}\n"
        text += f"  Пароль: {'✅ установлен' if pref.email_password else '❌ не установлен'}\n\n"
        text += "Используйте кнопки ниже для настройки."
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_preferences_menu())
        logger.info(f"Settings menu sent successfully")
    except Exception as e:
        logger.error(f"Error in show_settings: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при загрузке настроек: {str(e)}")


@router.message(F.text.regexp(r"^/notify_on$"))
async def notify_on(message: Message, db_user: User) -> None:
    async with async_session_maker() as session:
        pref_repo = UserPreferenceRepository(session)
        pref = await pref_repo.get_or_create(db_user.id)
        await pref_repo.set_notify(pref, True)
    await message.answer("🔔 Уведомления включены")


@router.message(F.text.regexp(r"^/notify_off$"))
async def notify_off(message: Message, db_user: User) -> None:
    async with async_session_maker() as session:
        pref_repo = UserPreferenceRepository(session)
        pref = await pref_repo.get_or_create(db_user.id)
        await pref_repo.set_notify(pref, False)
    await message.answer("🔕 Уведомления выключены")


@router.message(F.text.regexp(r"^/set_email\s+\S+@\S+\.[A-Za-z]{2,}$"))
async def set_email(message: Message, db_user: User) -> None:
    new_email = message.text.split(maxsplit=1)[1].strip()
    async with async_session_maker() as session:
        u_repo = UserRepository(session)
        db_user.contact_email = new_email
        await u_repo.update(db_user)
    await message.answer(f"📧 Email обновлен: {new_email}")


def _parse_list(arg: str) -> list[str]:
    return [item.strip() for item in arg.split(',') if item.strip()]


@router.message(F.text.regexp(r"^/set_customers\s+.+"))
async def set_customers(message: Message, db_user: User) -> None:
    payload = message.text.split(maxsplit=1)[1].strip()
    customers = _parse_list(payload)
    async with async_session_maker() as session:
        pref_repo = UserPreferenceRepository(session)
        pref = await pref_repo.get_or_create(db_user.id)
        await pref_repo.update_lists(pref, customers=customers)
    await message.answer("✅ Список заказчиков обновлен")


@router.message(F.text.regexp(r"^/set_nomenclature\s+.+"))
async def set_nomenclature(message: Message, db_user: User) -> None:
    payload = message.text.split(maxsplit=1)[1].strip()
    nomenclature = _parse_list(payload)
    async with async_session_maker() as session:
        pref_repo = UserPreferenceRepository(session)
        pref = await pref_repo.get_or_create(db_user.id)
        await pref_repo.update_lists(pref, nomenclature=nomenclature)
    await message.answer("✅ Список номенклатуры обновлен")


@router.message(F.text.regexp(r"^/show_prefs$"))
async def show_prefs(message: Message, db_user: User) -> None:
    async with async_session_maker() as session:
        pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
    text = "🔔 <b>Текущие настройки уведомлений</b>\n\n"
    text += f"Статус: {'✅ Включены' if pref.notify_enabled else '❌ Выключены'}\n"
    text += f"Заказчики: {', '.join(pref.customers or []) or 'все'}\n"
    text += f"Номенклатура: {', '.join(pref.nomenclature or []) or 'вся'}\n"
    await message.answer(text, parse_mode="HTML")
