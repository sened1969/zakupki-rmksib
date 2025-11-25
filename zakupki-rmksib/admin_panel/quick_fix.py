#!/usr/bin/env python
"""
Быстрое решение проблемы с кодировкой - временное использование SQLite
"""
import os
import sys
import django

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')

# Временно меняем БД на SQLite перед инициализацией Django
import django.conf
from django.conf import settings

# Меняем настройки БД на SQLite
settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    print("=" * 70)
    print("Быстрое решение: Использование SQLite вместо PostgreSQL")
    print("=" * 70)
    print("\nЭто временное решение для тестирования админ-панели.")
    print("SQLite не поддерживает все функции PostgreSQL (JSONField и т.д.).")
    print("Для продакшена нужно исправить проблему с PostgreSQL.\n")
    
    if len(sys.argv) == 1:
        print("Использование:")
        print("  python quick_fix.py migrate          # Применить миграции")
        print("  python quick_fix.py createsuperuser  # Создать суперпользователя")
        print("  python quick_fix.py runserver        # Запустить сервер")
        print("\nПример полной последовательности:")
        print("  python quick_fix.py migrate")
        print("  python quick_fix.py createsuperuser")
        print("  python quick_fix.py runserver")
    else:
        execute_from_command_line(['quick_fix.py'] + sys.argv[1:])

