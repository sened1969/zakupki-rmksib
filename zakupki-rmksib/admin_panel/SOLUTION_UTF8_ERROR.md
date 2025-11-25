# Решение ошибки UTF-8 при подключении к БД

## Проблема

```
'utf-8' codec can't decode byte 0xc2 in position 61: invalid continuation byte
```

Эта ошибка возникает, когда в пароле или других настройках подключения есть символы, которые не могут быть декодированы как UTF-8.

## Решение 1: Исправить пароль в .env файле (рекомендуется)

### Шаг 1: Откройте файл `.env` в корне проекта

Файл находится в: `C:\Users\sened\zakupki-rmksib\.env`

### Шаг 2: Найдите строку с паролем

Найдите строку:
```env
POSTGRES_PASSWORD=ваш_пароль_здесь
```

### Шаг 3: Замените пароль на ASCII-совместимый

**Проблемные символы:**
- Кириллица (русские буквы)
- Специальные символы (™, ©, и т.д.)
- Эмодзи

**Правильный пароль должен содержать только:**
- Латинские буквы (a-z, A-Z)
- Цифры (0-9)
- Стандартные символы (!@#$%^&*()_+-=[]{}|;:,.<>?)

**Примеры правильных паролей:**
```env
POSTGRES_PASSWORD=my_secure_password_123
POSTGRES_PASSWORD=Procure2025!
POSTGRES_PASSWORD=admin123
```

### Шаг 4: Сохраните файл в кодировке UTF-8

1. Откройте `.env` в текстовом редакторе (Notepad++, VS Code)
2. Сохраните как UTF-8 без BOM
3. Убедитесь, что нет лишних пробелов в начале/конце строк

### Шаг 5: Проверьте подключение

```bash
python check_db_connection.py
```

Если подключение успешно, вы увидите:
```
✅ Подключение успешно!
Версия PostgreSQL: ...
```

## Решение 2: Использовать переменные окружения напрямую

Если проблема сохраняется, установите переменные окружения напрямую:

### Windows PowerShell:

```powershell
# Установите переменные окружения
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
$env:POSTGRES_DB="procurement"
$env:POSTGRES_USER="procure_user"
$env:POSTGRES_PASSWORD="your_ascii_password_here"

# Проверьте подключение
python check_db_connection.py

# Запустите сервер
python manage.py runserver
```

### Windows CMD:

```cmd
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set POSTGRES_DB=procurement
set POSTGRES_USER=procure_user
set POSTGRES_PASSWORD=your_ascii_password_here

python check_db_connection.py
python manage.py runserver
```

## Решение 3: Временно использовать SQLite для тестирования

Если нужно быстро протестировать админ-панель без исправления PostgreSQL:

### Шаг 1: Используйте тестовый скрипт

```bash
# Применить миграции
python test_sqlite.py migrate

# Создать суперпользователя
python test_sqlite.py createsuperuser

# Запустить сервер
python test_sqlite.py runserver
```

### Шаг 2: Или временно измените settings.py

Откройте `admin_panel/admin_panel/settings.py` и найдите секцию `DATABASES`.

Временно замените на:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Затем:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**⚠️ Внимание:** SQLite не поддерживает все функции PostgreSQL. Это только для тестирования интерфейса админ-панели.

## Решение 4: Проверить кодировку файла .env

1. Откройте `.env` в VS Code или Notepad++
2. В VS Code: нажмите на кодировку в правом нижнем углу → "Reopen with Encoding" → выберите "UTF-8"
3. В Notepad++: Encoding → Convert to UTF-8
4. Сохраните файл

## Проверка решения

После исправления выполните:

```bash
# 1. Проверьте подключение
python check_db_connection.py

# 2. Если успешно, примените миграции
python manage.py migrate --run-syncdb

# 3. Создайте суперпользователя
python scripts/create_django_admin.py

# 4. Запустите сервер
python manage.py runserver

# 5. Откройте в браузере
# http://localhost:8000/admin/
```

## Дополнительная диагностика

Если проблема сохраняется, проверьте:

1. **Кодировку всех переменных:**
```python
import os
from dotenv import load_dotenv
load_dotenv()

password = os.getenv('POSTGRES_PASSWORD', '')
print(f"Длина пароля: {len(password)}")
print(f"Можно закодировать в UTF-8: {password.encode('utf-8', errors='strict')}")
```

2. **Проверьте, что PostgreSQL запущен:**
```bash
# Windows
netstat -ano | findstr :5432
```

3. **Попробуйте подключиться через psql:**
```bash
psql -h localhost -U procure_user -d procurement
```

## Рекомендация

**Лучшее решение:** Исправить пароль в `.env` файле, используя только ASCII символы. Это решит проблему раз и навсегда.

