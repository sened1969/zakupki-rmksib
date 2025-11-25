#!/usr/bin/env python
"""
Быстрый тест админ-панели с SQLite (без PostgreSQL)
Используйте это для тестирования интерфейса, если есть проблемы с PostgreSQL
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Временно меняем БД на SQLite
import django.conf
from django.conf import settings

# Сохраняем оригинальные настройки
original_db = settings.DATABASES['default'].copy()

# Меняем на SQLite
settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
}

django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    print("=" * 60)
    print("Тестирование админ-панели с SQLite")
    print("=" * 60)
    print("\nЭто временное решение для тестирования интерфейса.")
    print("SQLite не поддерживает все функции PostgreSQL.\n")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'migrate':
            print("Применение миграций...")
            execute_from_command_line(['manage.py', 'migrate'])
        elif command == 'createsuperuser':
            print("Создание суперпользователя...")
            execute_from_command_line(['manage.py', 'createsuperuser'])
        elif command == 'runserver':
            print("Запуск сервера...")
            print("Откройте http://localhost:8000/admin/ в браузере")
            execute_from_command_line(['manage.py', 'runserver'])
        else:
            execute_from_command_line(['manage.py'] + sys.argv[1:])
    else:
        print("Использование:")
        print("  python test_sqlite.py migrate          # Применить миграции")
        print("  python test_sqlite.py createsuperuser  # Создать суперпользователя")
        print("  python test_sqlite.py runserver        # Запустить сервер")

