#!/usr/bin/env python
"""Скрипт для управления миграциями Alembic (Windows-версия)"""
import sys
import subprocess
import os

def main():
    if len(sys.argv) < 2:
        print("Использование: python migrate.py {upgrade|downgrade|revision|history|current}")
        print("Примеры:")
        print("  python migrate.py upgrade              - применить все миграции")
        print('  python migrate.py revision "add users" - создать новую миграцию')
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    if command == "revision" and args:
        message = " ".join(args)
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", message])
    elif command == "upgrade":
        print("Применение миграций...")
        subprocess.run(["alembic", "upgrade", "head"])
    elif command == "downgrade":
        print("Откат миграций...")
        subprocess.run(["alembic", "downgrade", "-1"])
    elif command == "history":
        print("История миграций:")
        subprocess.run(["alembic", "history"])
    elif command == "current":
        print("Текущая версия БД:")
        subprocess.run(["alembic", "current"])
    else:
        print(f"Неизвестная команда: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()



















