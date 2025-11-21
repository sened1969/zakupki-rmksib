"""Утилиты для шифрования паролей"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
from loguru import logger

# Генерируем ключ из секрета в настройках или используем дефолтный
# В production должен быть в .env
ENCRYPTION_KEY_STR = os.getenv('ENCRYPTION_KEY', None)

if not ENCRYPTION_KEY_STR:
    # Генерируем ключ из фиксированной соли (для разработки)
    # В production должен быть установлен ENCRYPTION_KEY в .env
    logger.warning("ENCRYPTION_KEY not set, using default key (NOT SECURE FOR PRODUCTION)")
    salt = b'zakupki_rmksib_salt_2024'  # Фиксированная соль для разработки
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(b'default_password'))
    ENCRYPTION_KEY = key
else:
    # Используем ключ из .env
    ENCRYPTION_KEY = ENCRYPTION_KEY_STR.encode() if isinstance(ENCRYPTION_KEY_STR, str) else ENCRYPTION_KEY_STR

try:
    cipher_suite = Fernet(ENCRYPTION_KEY)
except Exception as e:
    logger.error(f"Failed to initialize encryption: {e}")
    # Fallback: генерируем новый ключ
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    logger.warning("Generated new encryption key. Existing encrypted data may not be decryptable.")


def encrypt_password(password: str) -> str:
    """
    Шифрует пароль для хранения в БД
    
    Args:
        password: Пароль в открытом виде
    
    Returns:
        Зашифрованный пароль (base64 строка)
    """
    if not password:
        return ""
    
    try:
        encrypted = cipher_suite.encrypt(password.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Error encrypting password: {e}")
        raise


def decrypt_password(encrypted_password: str) -> str:
    """
    Расшифровывает пароль из БД
    
    Args:
        encrypted_password: Зашифрованный пароль (base64 строка)
    
    Returns:
        Пароль в открытом виде
    """
    if not encrypted_password:
        return ""
    
    try:
        decrypted = cipher_suite.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting password: {e}")
        raise

