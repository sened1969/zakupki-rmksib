"""Административные команды"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database.models import User
from database import async_session_maker, UserRepository, UserPreferenceRepository

router = Router()


def is_admin(db_user: User) -> bool:
    """Проверка является ли пользователь администратором"""
    return db_user.role == "admin"


@router.message(Command("users"))
async def show_users(message: Message, db_user: User) -> None:
    """Показать список пользователей (только для админов)"""
    if not is_admin(db_user):
        await message.answer("⚠️ Эта команда доступна только администраторам.")
        return
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all_active(limit=50)
    
    if not users:
        await message.answer("📝 Пользователей пока нет.")
        return
    
    text = f"📋 <b>Активные пользователи ({len(users)}):</b>\n\n"
    for user in users:
        status = "✅ Активен" if user.is_active else "❌ Неактивен"
        role_emoji = {"user": "👤", "manager": "👨‍💼", "admin": "👑"}
        role = f"{role_emoji.get(user.role, '👤')} {user.role}"
        text += f"• {user.full_name or 'Без имени'}\n"
        text += f"  {role} | {status}\n"
        text += f"  ID: {user.telegram_id}\n\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("user_info"))
async def user_info(message: Message, db_user: User) -> None:
    """Информация о текущем пользователе"""
    text = f"👤 <b>Информация о вас:</b>\n\n"
    text += f"Имя: {db_user.full_name or 'Не указано'}\n"
    text += f"Username: @{db_user.username or 'Нет username'}\n"
    text += f"Telegram ID: {db_user.telegram_id}\n"
    text += f"Роль: {'👑 Администратор' if db_user.role == 'admin' else '👨‍💼 Менеджер' if db_user.role == 'manager' else '👤 Пользователь'}\n"
    text += f"Статус: {'✅ Активен' if db_user.is_active else '❌ Неактивен'}\n"
    text += f"Дата регистрации: {db_user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    if db_user.last_seen:
        text += f"Последний визит: {db_user.last_seen.strftime('%d.%m.%Y %H:%M')}"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("set_manager_role"))
async def set_manager_role(message: Message, db_user: User) -> None:
    """Выдать роль manager пользователю (только для админов)"""
    if not is_admin(db_user):
        await message.answer("⚠️ Эта команда доступна только администраторам.")
        return
    
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer(
            "Использование: /set_manager_role <telegram_id> <email> <full_name>\n\n"
            "Пример: /set_manager_role 6208324414 user@rmksib.ru \"Сергей\""
        )
        return
    
    try:
        telegram_id = int(parts[1])
        email = parts[2]
        full_name = parts[3]
    except ValueError:
        await message.answer("❌ Неверный формат telegram_id.")
        return
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        
        if user:
            user.role = "manager"
            user.contact_email = email
            user.full_name = full_name
            user = await user_repo.update(user)
            msg = f"✅ Пользователь {full_name} получил роль manager"
        else:
            user = await user_repo.create(
                telegram_id=telegram_id,
                full_name=full_name,
                contact_email=email,
                role="manager",
                is_active=True
            )
            pref_repo = UserPreferenceRepository(session)
            await pref_repo.get_or_create(user.id)
            msg = f"✅ Создан новый manager: {full_name}"
    
    await message.answer(msg)


@router.message(Command("set_role"))
async def set_role(message: Message, db_user: User) -> None:
    """Изменить роль пользователя (только для админов)"""
    if not is_admin(db_user):
        await message.answer("⚠️ Эта команда доступна только администраторам.")
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "Использование: /set_role <telegram_id> <role>\n\n"
            "Роли: user, manager, admin\n"
            "Пример: /set_role 6208324414 manager"
        )
        return
    
    try:
        telegram_id = int(parts[1])
        new_role = parts[2].lower()
    except ValueError:
        await message.answer("❌ Неверный формат telegram_id.")
        return
    
    if new_role not in ["user", "manager", "admin"]:
        await message.answer("❌ Неверная роль. Доступные: user, manager, admin")
        return
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            await message.answer(f"❌ Пользователь с ID {telegram_id} не найден.")
            return
        
        user = await user_repo.set_role(user, new_role)
        role_emoji = {"user": "👤", "manager": "👨‍💼", "admin": "👑"}
        await message.answer(f"✅ Роль изменена на {role_emoji.get(new_role, '👤')} {new_role}")
