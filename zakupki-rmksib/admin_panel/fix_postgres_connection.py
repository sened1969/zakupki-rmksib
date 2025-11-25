#!/usr/bin/env python
"""
Исправление проблемы подключения к PostgreSQL
"""
import os
import sys
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

print("=" * 70)
print("Исправление подключения к PostgreSQL")
print("=" * 70)

host = os.getenv('POSTGRES_HOST', 'localhost')
port = os.getenv('POSTGRES_PORT', '5432')
database = os.getenv('POSTGRES_DB', 'procurement')
user = os.getenv('POSTGRES_USER', 'procure_user')
password = os.getenv('POSTGRES_PASSWORD', 'change_me')

print(f"\nТекущие настройки:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  Database: {database}")
print(f"  User: {user}")
print(f"  Password: {'*' * len(password)}")

print("\n" + "=" * 70)
print("ПРОБЛЕМА: Ошибка аутентификации PostgreSQL")
print("=" * 70)
print("\nPostgreSQL возвращает сообщение об ошибке на русском языке:")
print("  'пользователь \"procure_user\" не прошел проверку подлинности (по паролю)'")
print("\nЭто означает, что:")
print("  1. Пользователь 'procure_user' не существует в PostgreSQL, ИЛИ")
print("  2. Пароль неверный")

print("\n" + "=" * 70)
print("РЕШЕНИЯ:")
print("=" * 70)

print("\nВариант 1: Создать пользователя в PostgreSQL")
print("-" * 70)
print("Подключитесь к PostgreSQL как суперпользователь (обычно 'postgres'):")
print(f"  psql -U postgres -d postgres")
print("\nЗатем выполните:")
print(f"  CREATE USER {user} WITH PASSWORD '{password}';")
print(f"  CREATE DATABASE {database} OWNER {user};")
print(f"  GRANT ALL PRIVILEGES ON DATABASE {database} TO {user};")
print(f"  \\q")

print("\nВариант 2: Использовать существующего пользователя")
print("-" * 70)
print("Если у вас уже есть пользователь PostgreSQL:")
print("1. Узнайте правильный пароль")
print("2. Обновите файл .env:")
print(f"   POSTGRES_USER=ваш_пользователь")
print(f"   POSTGRES_PASSWORD=ваш_пароль")

print("\nВариант 3: Использовать стандартного пользователя postgres")
print("-" * 70)
print("Временно используйте стандартного пользователя:")
print("1. Откройте .env файл")
print("2. Измените:")
print("   POSTGRES_USER=postgres")
print("   POSTGRES_PASSWORD=ваш_пароль_postgres")
print("3. Перезапустите проверку: python check_db_connection.py")

print("\nВариант 4: Использовать SQLite для тестирования (уже работает)")
print("-" * 70)
print("Админ-панель уже работает с SQLite:")
print("  http://localhost:8000/admin/")
print("  Username: admin")
print("  Password: admin123")
print("\nДля продакшена все равно нужно настроить PostgreSQL.")

print("\n" + "=" * 70)
print("БЫСТРОЕ РЕШЕНИЕ: Создание пользователя через psql")
print("=" * 70)
print("\nВыполните в терминале:")
print(f"psql -U postgres")
print("\nЗатем в psql:")
print(f"CREATE USER {user} WITH PASSWORD '{password}';")
print(f"CREATE DATABASE {database} OWNER {user};")
print(f"GRANT ALL PRIVILEGES ON DATABASE {database} TO {user};")
print("\\q")

