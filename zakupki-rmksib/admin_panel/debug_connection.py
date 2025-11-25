#!/usr/bin/env python
"""
Расширенная диагностика проблемы подключения к PostgreSQL
"""
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

print("=" * 70)
print("Расширенная диагностика подключения к PostgreSQL")
print("=" * 70)

# Получаем все параметры
host = os.getenv('POSTGRES_HOST', 'localhost')
port = os.getenv('POSTGRES_PORT', '5432')
database = os.getenv('POSTGRES_DB', 'procurement')
user = os.getenv('POSTGRES_USER', 'procure_user')
password = os.getenv('POSTGRES_PASSWORD', 'change_me')

print("\n1. Проверка параметров подключения:")
print(f"   Host: {host} (тип: {type(host).__name__})")
print(f"   Port: {port} (тип: {type(port).__name__})")
print(f"   Database: {database} (тип: {type(database).__name__})")
print(f"   User: {user} (тип: {type(user).__name__})")
print(f"   Password: {'*' * len(password)} (длина: {len(password)})")

print("\n2. Проверка кодировки каждого параметра:")
for name, value in [('host', host), ('port', port), ('database', database), ('user', user), ('password', password)]:
    try:
        encoded = value.encode('utf-8')
        print(f"   {name}: ✅ UTF-8 OK (длина байт: {len(encoded)})")
        if len(encoded) > 50:
            print(f"      Первые 50 байт: {encoded[:50]}")
    except UnicodeEncodeError as e:
        print(f"   {name}: ❌ Ошибка UTF-8: {e}")
        print(f"      Значение (repr): {repr(value)}")

print("\n3. Попытка подключения разными способами:")

try:
    import psycopg2
    print("   ✅ psycopg2 установлен")
except ImportError:
    print("   ❌ psycopg2 не установлен")
    print("   Установите: pip install psycopg2-binary")
    sys.exit(1)

# Способ 1: Прямое подключение
print("\n   Способ 1: Прямое подключение с явной кодировкой...")
try:
    conn = psycopg2.connect(
        host=str(host),
        port=int(port),
        database=str(database),
        user=str(user),
        password=str(password),
        client_encoding='UTF8',
        connect_timeout=5
    )
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"   ✅ Успешно! Версия: {version[0][:50]}...")
    cursor.close()
    conn.close()
    print("\n" + "=" * 70)
    print("✅ ПОДКЛЮЧЕНИЕ УСПЕШНО!")
    print("=" * 70)
    sys.exit(0)
except UnicodeDecodeError as e:
    print(f"   ❌ UnicodeDecodeError: {e}")
    print(f"      Позиция ошибки: {e.args}")
except Exception as e:
    print(f"   ❌ Ошибка: {type(e).__name__}: {e}")

# Способ 2: DSN строка
print("\n   Способ 2: Использование DSN строки...")
try:
    # Создаем DSN с явным указанием кодировки
    dsn_parts = [
        f"host={host}",
        f"port={port}",
        f"dbname={database}",
        f"user={user}",
        f"password={password}",
        "client_encoding=UTF8"
    ]
    dsn = " ".join(dsn_parts)
    print(f"   DSN (первые 100 символов): {dsn[:100]}...")
    
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"   ✅ Успешно! Версия: {version[0][:50]}...")
    cursor.close()
    conn.close()
    print("\n" + "=" * 70)
    print("✅ ПОДКЛЮЧЕНИЕ УСПЕШНО (через DSN)!")
    print("=" * 70)
    sys.exit(0)
except Exception as e:
    print(f"   ❌ Ошибка: {type(e).__name__}: {e}")

# Способ 3: Подключение через psycopg2.extensions
print("\n   Способ 3: Использование psycopg2.extensions...")
try:
    from psycopg2 import extensions
    conn = psycopg2.connect(
        host=str(host),
        port=int(port),
        database=str(database),
        user=str(user),
        password=str(password)
    )
    # Устанавливаем кодировку после подключения
    conn.set_client_encoding('UTF8')
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"   ✅ Успешно! Версия: {version[0][:50]}...")
    cursor.close()
    conn.close()
    print("\n" + "=" * 70)
    print("✅ ПОДКЛЮЧЕНИЕ УСПЕШНО (через extensions)!")
    print("=" * 70)
    sys.exit(0)
except Exception as e:
    print(f"   ❌ Ошибка: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("❌ ВСЕ СПОСОБЫ ПОДКЛЮЧЕНИЯ НЕУДАЧНЫ")
print("=" * 70)
print("\nВозможные причины:")
print("1. PostgreSQL не запущен")
print("2. Неправильные учетные данные")
print("3. Проблема с кодировкой в системных переменных окружения")
print("4. Файрвол блокирует подключение")
print("\nРекомендации:")
print("1. Проверьте, запущен ли PostgreSQL: netstat -ano | findstr :5432")
print("2. Попробуйте подключиться через psql:")
print(f"   psql -h {host} -p {port} -U {user} -d {database}")
print("3. Используйте SQLite для тестирования: python quick_fix.py runserver")

