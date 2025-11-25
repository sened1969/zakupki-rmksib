#!/usr/bin/env python
"""
Скрипт для проверки подключения к базе данных
"""
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения из корня проекта
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

print("Проверка настроек подключения к БД:")
print(f"POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'не установлен')}")
print(f"POSTGRES_PORT: {os.getenv('POSTGRES_PORT', 'не установлен')}")
print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB', 'не установлен')}")
print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER', 'не установлен')}")
print(f"POSTGRES_PASSWORD: {'*' * len(os.getenv('POSTGRES_PASSWORD', '')) if os.getenv('POSTGRES_PASSWORD') else 'не установлен'}")

try:
    import psycopg2
    print("\nПопытка подключения к БД...")
    
    # Получаем параметры подключения
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DB', 'procurement')
    user = os.getenv('POSTGRES_USER', 'procure_user')
    password = os.getenv('POSTGRES_PASSWORD', 'change_me')
    
    # Проверяем кодировку пароля
    try:
        password.encode('utf-8')
    except UnicodeEncodeError as e:
        print(f"⚠️  Проблема с кодировкой пароля: {e}")
        print("   Пароль содержит символы, которые не могут быть закодированы в UTF-8")
        print("   Решение: используйте только ASCII символы в пароле (латинские буквы, цифры)")
        sys.exit(1)
    
    # Пробуем подключиться разными способами
    try:
        # Способ 1: Прямое подключение с явной кодировкой
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password.encode('utf-8').decode('utf-8'),  # Убеждаемся в UTF-8
            client_encoding='UTF8',
            connect_timeout=5
        )
    except UnicodeDecodeError:
        # Способ 2: Используем DSN строку
        dsn = f"host={host} port={port} dbname={database} user={user} password={password} client_encoding=UTF8"
        conn = psycopg2.connect(dsn)
    except Exception as e:
        # Способ 3: Пробуем с явным указанием кодировки в опциях
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password,
            options='-c client_encoding=UTF8'
        )
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ Подключение успешно!")
    print(f"Версия PostgreSQL: {version[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    print("\nВозможные решения:")
    print("1. Убедитесь, что PostgreSQL запущен")
    print("2. Проверьте настройки в .env файле")
    print("3. Проверьте права доступа пользователя БД")

