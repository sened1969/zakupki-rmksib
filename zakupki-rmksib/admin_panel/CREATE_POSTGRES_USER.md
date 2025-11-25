# Создание пользователя PostgreSQL

## Проблема

Ошибка: `пользователь "procure_user" не прошел проверку подлинности (по паролю)`

Это означает, что пользователь `procure_user` не существует в PostgreSQL или пароль неверный.

## Решение: Создать пользователя и базу данных

### Шаг 1: Подключитесь к PostgreSQL как суперпользователь

Обычно это пользователь `postgres`:

```bash
psql -U postgres
```

Если запросит пароль, введите пароль пользователя `postgres`.

### Шаг 2: Создайте пользователя и базу данных

В psql выполните следующие команды:

```sql
-- Создать пользователя
CREATE USER procure_user WITH PASSWORD 'change_me';

-- Создать базу данных
CREATE DATABASE procurement OWNER procure_user;

-- Дать все права на базу данных
GRANT ALL PRIVILEGES ON DATABASE procurement TO procure_user;

-- Выйти из psql
\q
```

### Шаг 3: Проверьте подключение

```bash
python check_db_connection.py
```

Если все правильно, вы увидите:
```
✅ Подключение успешно!
Версия PostgreSQL: ...
```

### Шаг 4: Примените миграции Django

```bash
python manage.py migrate --run-syncdb
```

### Шаг 5: Создайте суперпользователя Django

```bash
python scripts/create_django_admin.py
```

### Шаг 6: Запустите сервер

```bash
python manage.py runserver
```

## Альтернатива: Использовать существующего пользователя

Если у вас уже есть пользователь PostgreSQL:

1. Откройте файл `.env` в корне проекта
2. Измените настройки:
```env
POSTGRES_USER=ваш_существующий_пользователь
POSTGRES_PASSWORD=ваш_пароль
```
3. Проверьте подключение: `python check_db_connection.py`

## Альтернатива: Использовать стандартного пользователя postgres

Если хотите использовать стандартного пользователя `postgres`:

1. Откройте файл `.env`
2. Измените:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=ваш_пароль_postgres
```
3. Проверьте подключение: `python check_db_connection.py`

**⚠️ Внимание:** Использование пользователя `postgres` не рекомендуется для продакшена из соображений безопасности.

## Текущий статус

Админ-панель уже работает с SQLite:
- URL: http://localhost:8000/admin/
- Username: `admin`
- Password: `admin123`

Для продакшена нужно настроить PostgreSQL.

