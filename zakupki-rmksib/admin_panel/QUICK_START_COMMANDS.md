# Быстрый старт - Правильные команды

## ⚠️ Важно: Вы должны находиться в директории `admin_panel/`

Все команды нужно выполнять из директории `admin_panel/`, а не из корня проекта!

## Правильная последовательность команд

### Шаг 1: Перейдите в директорию admin_panel

```bash
cd admin_panel
```

### Шаг 2: Проверьте подключение к БД

```bash
python check_db_connection.py
```

### Шаг 3: Примените миграции

```bash
python manage.py migrate --run-syncdb
```

### Шаг 4: Создайте суперпользователя

```bash
python scripts/create_django_admin.py
```

### Шаг 5: Запустите сервер

```bash
python manage.py runserver
```

### Шаг 6: Откройте в браузере

```
http://localhost:8000/admin/
```

## Полная последовательность (скопируйте и выполните)

```bash
# Перейти в директорию админ-панели
cd admin_panel

# Проверить подключение к БД
python check_db_connection.py

# Применить миграции
python manage.py migrate --run-syncdb

# Создать суперпользователя
python scripts/create_django_admin.py

# Запустить сервер
python manage.py runserver
```

## Если вы находитесь в корне проекта

Если вы находитесь в `~/zakupki-rmksib/`, используйте полные пути:

```bash
# Проверить подключение к БД
python admin_panel/check_db_connection.py

# Применить миграции
cd admin_panel && python manage.py migrate --run-syncdb

# Создать суперпользователя
cd admin_panel && python scripts/create_django_admin.py

# Запустить сервер
cd admin_panel && python manage.py runserver
```

## Проверка текущей директории

Чтобы проверить, где вы находитесь:

```bash
pwd
```

Вы должны увидеть что-то вроде:
```
/c/Users/sened/zakupki-rmksib/admin_panel
```

Если вы видите:
```
/c/Users/sened/zakupki-rmksib
```

То нужно перейти в `admin_panel`:
```bash
cd admin_panel
```

## Структура файлов

```
zakupki-rmksib/              ← Корень проекта
├── admin_panel/             ← Директория Django проекта
│   ├── manage.py           ← Здесь находится manage.py
│   ├── check_db_connection.py
│   └── scripts/
│       └── create_django_admin.py
└── ...
```

## Решение проблем

### Ошибка: "No such file or directory"
- Убедитесь, что вы находитесь в директории `admin_panel/`
- Проверьте: `pwd` должен показывать путь с `admin_panel` в конце
- Перейдите: `cd admin_panel`

### Ошибка: "can't open file 'manage.py'"
- Вы находитесь не в той директории
- Выполните: `cd admin_panel`
- Затем: `python manage.py ...`

### Ошибка подключения к БД
- См. `FIX_DB_CONNECTION.md` для решения проблем с БД

