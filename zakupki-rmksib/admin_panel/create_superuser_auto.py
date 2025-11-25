#!/usr/bin/env python
"""
Автоматическое создание суперпользователя для SQLite
"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')

# Используем SQLite
import django.conf
from django.conf import settings
settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = 'admin'
email = 'admin@example.com'
password = 'admin123'

if User.objects.filter(username=username).exists():
    print(f"Пользователь {username} уже существует!")
    print("Используйте эти данные для входа:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print("✅ Суперпользователь успешно создан!")
    print("\nДанные для входа:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"\nОткройте в браузере: http://localhost:8000/admin/")

