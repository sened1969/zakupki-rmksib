#!/usr/bin/env python
"""Скрипт инициализации пользователей"""
import asyncio
import sys
from database import async_session_maker, UserRepository, UserPreferenceRepository


# Список пользователей для инициализации
USERS = [
    {"telegram_id": 0, "full_name": "Павел", "email": "sp@rmksib.ru", "role": "manager"},
    {"telegram_id": 0, "full_name": "Ольга", "email": "bo@rmksib.ru", "role": "manager"},
    {"telegram_id": 0, "full_name": "Екатерина", "email": "info@rmksib.ru", "role": "manager"},
    {"telegram_id": 6208324414, "full_name": "Сергей", "email": "sened17@yandex.ru", "role": "manager"},
]


async def init_users():
    """Инициализировать пользователей"""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        pref_repo = UserPreferenceRepository(session)
        
        print("Создание пользователей...")
        for user_data in USERS:
            telegram_id = user_data.get("telegram_id")
            if telegram_id == 0:
                print(f"⚠️ Пропущен {user_data['full_name']} - не указан telegram_id")
                continue
            
            # Проверяем существование
            user = await user_repo.get_by_telegram_id(telegram_id)
            
            if user:
                print(f"ℹ️ Пользователь {user_data['full_name']} уже существует, обновление...")
                user.full_name = user_data["full_name"]
                user.contact_email = user_data["email"]
                user.role = user_data["role"]
                await user_repo.update(user)
            else:
                print(f"➕ Создание пользователя {user_data['full_name']}...")
                user = await user_repo.create(
                    telegram_id=telegram_id,
                    full_name=user_data["full_name"],
                    contact_email=user_data["email"],
                    role=user_data["role"],
                    is_active=True
                )
                print(f"   ID: {user.id}, Telegram ID: {user.telegram_id}")
            
            # Создаем предпочтения
            await pref_repo.get_or_create(user.id)
        
        print("\n✅ Инициализация завершена!")
        print("\nДля инициализации через бота используйте:")
        print("เค  /set_manager_role <telegram_id> <email> <full_name>")


async def main():
    if len(sys.argv) > 1:
        print("Использование: python scripts/init_users.py")
        print("\nПримечание: заполните telegram_id в скрипте перед запуском.")
        print("Или используйте команду бота: /set_manager_role")
        sys.exit(1)
    
    print("⚠️ Важно: перед запуском заполните telegram_id для каждого пользователя в файле scripts/init_users.py")
    print("\nДля получения telegram_id пользователя:")
    print("1. Попросите пользователя написать боту /start")
    print("2. Используйте команду /users для просмотра ID")
    print("\nЗапустить инициализацию? (y/n): ", end="")
    
    response = input().strip().lower()
    if response != "y":
        print("Отменено.")
        return
    
    await init_users()


if __name__ == "__main__":
    asyncio.run(main())


