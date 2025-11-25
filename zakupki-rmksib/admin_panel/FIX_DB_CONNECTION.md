# Решение проблемы подключения к БД

## Проблема: UnicodeDecodeError при подключении к PostgreSQL

Ошибка:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc2 in position 61
```

Это означает, что в настройках подключения (скорее всего в пароле) есть символы, которые не могут быть декодированы как UTF-8.

## Решение

### Вариант 1: Проверьте пароль в .env файле

1. Откройте файл `.env` в корне проекта (не в `admin_panel/`)
2. Проверьте строку `POSTGRES_PASSWORD`
3. Убедитесь, что пароль содержит только ASCII символы (латинские буквы, цифры, стандартные символы)
4. Если есть кириллица или специальные символы, замените их

Пример правильного пароля:
```env
POSTGRES_PASSWORD=my_secure_password_123
```

Пример неправильного пароля (может вызвать проблемы):
```env
POSTGRES_PASSWORD=пароль123  # кириллица
POSTGRES_PASSWORD=password™  # специальные символы
```

### Вариант 2: Используйте SQLite для тестирования (временно)

Если нужно быстро протестировать админ-панель без PostgreSQL:

1. **Измените `admin_panel/admin_panel/settings.py`:**

Найдите секцию `DATABASES` и замените на:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

2. **Примените миграции:**
```bash
python manage.py migrate
```

3. **Создайте суперпользователя:**
```bash
python manage.py createsuperuser
```

4. **Запустите сервер:**
```bash
python manage.py runserver
```

**⚠️ Внимание:** SQLite не поддерживает все функции PostgreSQL (например, JSONField может работать по-другому). Это только для тестирования интерфейса админ-панели.

### Вариант 3: Исправьте кодировку файла .env

1. Откройте `.env` файл в текстовом редакторе
2. Сохраните его с кодировкой UTF-8 без BOM
3. Убедитесь, что все значения в кавычках (если используются)

### Вариант 4: Используйте переменные окружения напрямую

Вместо чтения из `.env`, установите переменные окружения напрямую:

**Windows PowerShell:**
```powershell
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
$env:POSTGRES_DB="procurement"
$env:POSTGRES_USER="procure_user"
$env:POSTGRES_PASSWORD="your_password_here"
python manage.py runserver
```

**Windows CMD:**
```cmd
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set POSTGRES_DB=procurement
set POSTGRES_USER=procure_user
set POSTGRES_PASSWORD=your_password_here
python manage.py runserver
```

**Linux/Mac:**
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=procurement
export POSTGRES_USER=procure_user
export POSTGRES_PASSWORD=your_password_here
python manage.py runserver
```

## Проверка подключения

После исправления проверьте подключение:

```bash
python check_db_connection.py
```

Если подключение успешно, вы увидите:
```
✅ Подключение успешно!
Версия PostgreSQL: ...
```

## После исправления

1. Примените миграции:
```bash
python manage.py migrate --run-syncdb
```

2. Создайте суперпользователя:
```bash
python scripts/create_django_admin.py
```

3. Запустите сервер:
```bash
python manage.py runserver
```

4. Откройте в браузере:
```
http://localhost:8000/admin/
```

