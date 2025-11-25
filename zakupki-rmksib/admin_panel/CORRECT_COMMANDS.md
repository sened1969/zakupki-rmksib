# Правильные команды для работы с админ-панелью

## ⚠️ Важно: Правильная директория

Вы должны находиться в директории `admin_panel/`, а НЕ в `admin_panel/admin_panel/`

## Проверка текущей директории

Выполните:
```bash
pwd
```

Вы должны увидеть:
```
/c/Users/sened/zakupki-rmksib/admin_panel
```

**НЕ должно быть:**
```
/c/Users/sened/zakupki-rmksib/admin_panel/admin_panel  ❌
```

## Если вы в неправильной директории

### Вариант 1: Вернуться на уровень выше
```bash
cd ..
```

### Вариант 2: Перейти в правильную директорию из корня проекта
```bash
cd zakupki-rmksib/admin_panel
```

## Правильная последовательность команд

### Шаг 1: Убедитесь, что вы в правильной директории
```bash
pwd
# Должно показать: /c/Users/sened/zakupki-rmksib/admin_panel
```

Если нет, перейдите:
```bash
cd zakupki-rmksib/admin_panel
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

## Структура директорий

```
zakupki-rmksib/                    ← Корень проекта
└── admin_panel/                   ← ВЫ ДОЛЖНЫ БЫТЬ ЗДЕСЬ ✅
    ├── manage.py                  ← Здесь находится manage.py
    ├── check_db_connection.py     ← Здесь находится скрипт проверки
    ├── admin_panel/               ← НЕ ЗАХОДИТЕ СЮДА ❌
    │   ├── settings.py
    │   └── urls.py
    └── procurement/
```

## Быстрая проверка

Если команда `ls` показывает файлы `manage.py` и `check_db_connection.py`, вы в правильной директории.

Если команда `ls` показывает только `settings.py` и `urls.py`, вы в неправильной директории - выполните `cd ..`

