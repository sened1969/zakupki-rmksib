# Быстрый старт Django Admin Panel

## 🚀 Запуск через Docker (рекомендуется)

```bash
# Запустить все сервисы
docker compose up -d

# Создать суперпользователя
docker compose exec admin_panel python scripts/create_django_admin.py

# Открыть в браузере
# http://localhost:8000/admin/
```

## 💻 Локальный запуск

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Перейти в директорию админ-панели
cd admin_panel

# 3. Применить миграции
python manage.py migrate --run-syncdb

# 4. Создать суперпользователя
python scripts/create_django_admin.py

# 5. Запустить сервер
python manage.py runserver

# 6. Открыть в браузере
# http://localhost:8000/admin/
```

## 📝 Первый вход

1. Откройте http://localhost:8000/admin/
2. Введите логин и пароль, созданные через скрипт
3. Начните управлять данными!

## 🔧 Настройка .env

Убедитесь, что в `.env` файле есть:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=procurement
POSTGRES_USER=procure_user
POSTGRES_PASSWORD=change_me

DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

## 📚 Подробная документация

См. `admin_panel/README.md` и `ADMIN_PANEL_SETUP.md`

