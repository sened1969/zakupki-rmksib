# Немедленное решение: Запуск админ-панели с SQLite

## Проблема
Ошибка подключения к PostgreSQL из-за проблем с кодировкой или PostgreSQL не запущен.

## Быстрое решение: Использовать SQLite (для тестирования)

### Вариант 1: Использовать скрипт quick_fix.py

```bash
# 1. Применить миграции
python quick_fix.py migrate

# 2. Создать суперпользователя
python quick_fix.py createsuperuser

# 3. Запустить сервер
python quick_fix.py runserver
```

Затем откройте в браузере: http://localhost:8000/admin/

### Вариант 2: Временно изменить settings.py

1. Откройте файл `admin_panel/admin_panel/settings.py`

2. Найдите секцию `DATABASES` (около строки 70)

3. Временно замените на:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

4. Сохраните файл

5. Выполните команды:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

6. Откройте http://localhost:8000/admin/

### ⚠️ Важно

- SQLite не поддерживает все функции PostgreSQL (JSONField может работать по-другому)
- Это только для тестирования интерфейса админ-панели
- Для продакшена нужно исправить проблему с PostgreSQL

## После тестирования

Чтобы вернуться к PostgreSQL:

1. Верните оригинальные настройки БД в `settings.py`
2. Исправьте проблему с кодировкой (см. `SOLUTION_UTF8_ERROR.md`)
3. Убедитесь, что PostgreSQL запущен
4. Примените миграции: `python manage.py migrate --run-syncdb`

