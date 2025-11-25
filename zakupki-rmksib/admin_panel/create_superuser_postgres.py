#!/usr/bin/env python
"""
Автоматическое создание суперпользователя для PostgreSQL
"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = 'admin'
email = 'admin@example.com'
password = 'admin123'

if User.objects.filter(username=username).exists():
    print(f"✅ Пользователь {username} уже существует!")
    print("\nДанные для входа:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"\nОткройте в браузере: http://localhost:8000/admin/")
else:
    try:
        User.objects.create_superuser(username=username, email=email, password=password)
        print("✅ Суперпользователь успешно создан!")
        print("\nДанные для входа:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"\nОткройте в браузере: http://localhost:8000/admin/")
    except Exception as e:
        print(f"❌ Ошибка при создании суперпользователя: {e}")
        print("\nПопробуйте создать вручную:")
        print("  python manage.py createsuperuser")

