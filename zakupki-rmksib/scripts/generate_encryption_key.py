#!/usr/bin/env python3
"""
Скрипт для генерации безопасного ключа шифрования

Использование:
    python scripts/generate_encryption_key.py

Скопируйте сгенерированный ключ в .env файл:
    ENCRYPTION_KEY=сгенерированный_ключ
"""
from cryptography.fernet import Fernet

def generate_encryption_key():
    """Генерирует безопасный ключ шифрования для Fernet"""
    key = Fernet.generate_key()
    return key.decode()

if __name__ == "__main__":
    print("=" * 60)
    print("Генерация ключа шифрования для ENCRYPTION_KEY")
    print("=" * 60)
    print()
    
    key = generate_encryption_key()
    
    print("✅ Ключ успешно сгенерирован!")
    print()
    print("Добавьте следующую строку в ваш .env файл:")
    print("-" * 60)
    print(f"ENCRYPTION_KEY={key}")
    print("-" * 60)
    print()
    print("⚠️  ВАЖНО:")
    print("1. Сохраните этот ключ в безопасном месте")
    print("2. НЕ коммитьте .env файл в Git")
    print("3. При изменении ключа все зашифрованные пароли станут недоступны")
    print("4. Используйте один и тот же ключ на всех серверах")
    print()
    print("=" * 60)

