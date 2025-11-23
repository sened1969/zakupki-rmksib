#!/bin/bash
# Скрипт для управления миграциями Alembic

case "$1" in
    upgrade)
        echo "Применение миграций..."
        alembic upgrade head
        ;;
    downgrade)
        echo "Откат миграций..."
        alembic downgrade -1
        ;;
    revision)
        echo "Создание новой миграции: $2"
        alembic revision --autogenerate -m "$2"
        ;;
    history)
        echo "История миграций:"
        alembic history
        ;;
    current)
        echo "Текущая версия БД:"
        alembic current
        ;;
    *)
        echo "Использование: $0 {upgrade|downgrade|revision|history|current}"
        echo "Примеры:"
        echo "  $0 upgrade           - применить все миграции"
        echo "  $0 revision 'add users'  - создать новую миграцию"
        exit 1
        ;;
esac























