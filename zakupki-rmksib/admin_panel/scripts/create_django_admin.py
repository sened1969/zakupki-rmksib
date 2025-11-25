#!/usr/bin/env python
"""
Скрипт для создания суперпользователя Django админ-панели
"""
import os
import sys
import django

# Добавляем путь к проекту (admin_panel директория)
admin_panel_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, admin_panel_dir)
os.chdir(admin_panel_dir)  # Переходим в директорию admin_panel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    """Создание суперпользователя"""
    username = input("Введите имя пользователя (admin): ").strip() or "admin"
    email = input("Введите email: ").strip()
    
    if User.objects.filter(username=username).exists():
        print(f"Пользователь {username} уже существует!")
        return
    
    password = input("Введите пароль: ").strip()
    if not password:
        print("Пароль не может быть пустым!")
        return
    
    try:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"\n✅ Суперпользователь {username} успешно создан!")
        print(f"   Email: {email}")
        print(f"\nТеперь вы можете войти в админ-панель:")
        print(f"   URL: http://localhost:8000/admin/")
        print(f"   Username: {username}")
    except Exception as e:
        print(f"❌ Ошибка при создании суперпользователя: {e}")

if __name__ == "__main__":
    create_superuser()

