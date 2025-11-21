"""Сервис отправки email от имени менеджера с его настройками SMTP"""
from __future__ import annotations
from email.message import EmailMessage
from typing import Iterable, Optional
from loguru import logger
import aiosmtplib
from utils.encryption import decrypt_password


class ManagerEmailService:
    """Сервис для отправки email с использованием настроек менеджера"""
    
    # Конфигурация SMTP для разных провайдеров
    SMTP_CONFIGS = {
        "yandex": {
            "server": "smtp.yandex.ru",
            "port": 465,
            "use_tls": True,
            "start_tls": False
        },
        "gmail": {
            "server": "smtp.gmail.com",
            "port": 587,
            "use_tls": False,
            "start_tls": True
        },
        "mailru": {
            "server": "smtp.mail.ru",
            "port": 465,
            "use_tls": True,
            "start_tls": False
        }
    }
    
    def __init__(
        self,
        email: str,
        password: str,  # Зашифрованный пароль
        smtp_provider: str = "yandex"
    ):
        """
        Инициализация сервиса
        
        Args:
            email: Email адрес менеджера
            password: Зашифрованный пароль приложения
            smtp_provider: Провайдер SMTP (yandex, gmail, mailru)
        """
        self.email = email
        self.encrypted_password = password
        self.smtp_provider = smtp_provider.lower()
        self.config = self.SMTP_CONFIGS.get(self.smtp_provider, self.SMTP_CONFIGS["yandex"])
    
    def _get_password(self) -> str:
        """Расшифровывает пароль"""
        try:
            return decrypt_password(self.encrypted_password)
        except Exception as e:
            logger.error(f"Error decrypting password: {e}")
            raise
    
    async def send_email(
        self,
        subject: str,
        body_html: str,
        recipients: Iterable[str],
        body_text: Optional[str] = None
    ) -> bool:
        """
        Отправляет HTML email получателям
        
        Args:
            subject: Тема письма
            body_html: HTML тело письма
            recipients: Список получателей
            body_text: Текстовое тело письма (опционально)
        
        Returns:
            True если отправка успешна, False иначе
        """
        recipients = [r for r in recipients if r]
        if not recipients:
            logger.warning("No recipients provided")
            return False
        
        if not self.email or not self.encrypted_password:
            logger.warning("Email or password not configured")
            return False
        
        try:
            password = self._get_password()
        except:
            logger.error("Failed to decrypt password")
            return False
        
        message = EmailMessage()
        message["From"] = self.email
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        
        # Устанавливаем текстовую версию
        if body_text:
            message.set_content(body_text)
        else:
            message.set_content("This message requires an HTML-capable mail client.")
        
        # Добавляем HTML версию
        message.add_alternative(body_html, subtype="html")
        
        try:
            # Для порта 465 используем SSL, для 587 - TLS
            if self.config["port"] == 465:
                # Порт 465 требует SSL соединения
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.config["server"],
                    port=self.config["port"],
                    use_tls=True  # SSL для порта 465
                )
            else:
                # Порт 587 использует STARTTLS
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.config["server"],
                    port=self.config["port"],
                    use_tls=False
                )
            
            async with smtp_client:
                await smtp_client.connect()
                
                if self.config["start_tls"]:
                    await smtp_client.starttls()
                
                await smtp_client.login(self.email, password)
                await smtp_client.send_message(message)
            
            logger.info(f"Email sent successfully from {self.email} to {recipients}")
            return True
            
        except aiosmtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed for {self.email}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Failed to send email from {self.email}: {e}")
            return False
    
    async def test_connection(self) -> tuple[bool, str]:
        """
        Тестирует подключение к SMTP серверу
        
        Returns:
            Кортеж (успех, сообщение)
        """
        if not self.email or not self.encrypted_password:
            return False, "Email или пароль не настроены"
        
        try:
            password = self._get_password()
            if not password:
                return False, "Пароль пустой после расшифровки"
            logger.info(f"Password decrypted successfully, length: {len(password)}")
        except Exception as e:
            logger.error(f"Error decrypting password: {e}", exc_info=True)
            return False, f"Ошибка расшифровки пароля: {e}"
        
        logger.info(f"Testing SMTP connection: {self.email} @ {self.config['server']}:{self.config['port']} (provider: {self.smtp_provider})")
        logger.info(f"SMTP config: use_tls={self.config['use_tls']}, start_tls={self.config['start_tls']}")
        
        try:
            # Для порта 465 используем SSL, для 587 - TLS
            if self.config["port"] == 465:
                # Порт 465 требует SSL соединения
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.config["server"],
                    port=self.config["port"],
                    use_tls=True  # SSL для порта 465
                )
            else:
                # Порт 587 использует STARTTLS
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.config["server"],
                    port=self.config["port"],
                    use_tls=False
                )
            
            async with smtp_client:
                logger.info(f"Connecting to {self.config['server']}:{self.config['port']}...")
                await smtp_client.connect()
                logger.info("Connected successfully")
                
                if self.config["start_tls"]:
                    logger.info("Starting TLS...")
                    await smtp_client.starttls()
                    logger.info("TLS started")
                
                logger.info(f"Attempting login with email: {self.email}")
                await smtp_client.login(self.email, password)
                logger.info("Login successful!")
            
            return True, "Подключение успешно"
            
        except aiosmtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            logger.error(f"Email: {self.email}, Provider: {self.smtp_provider}, Server: {self.config['server']}:{self.config['port']}")
            
            error_msg = str(e)
            # Специальная обработка ошибки доступа Yandex
            if "does not have access rights" in error_msg or "access rights" in error_msg.lower():
                return False, (
                    "❌ <b>Ошибка доступа к SMTP</b>\n\n"
                    "У вашего аккаунта Yandex не включен доступ к почтовым программам.\n\n"
                    "<b>Как исправить:</b>\n"
                    "1. Откройте https://id.yandex.ru/security\n"
                    "2. Войдите в аккаунт sened17@yandex.ru\n"
                    "3. Найдите раздел 'Доступ к аккаунту'\n"
                    "4. Включите 'Доступ к почтовым программам'\n"
                    "5. Сохраните изменения\n"
                    "6. Попробуйте проверить подключение снова\n\n"
                    f"<i>Детали ошибки: {error_msg}</i>"
                )
            
            return False, f"Ошибка аутентификации. Проверьте email и пароль приложения.\n\nДетали: {error_msg}"
        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}", exc_info=True)
            return False, f"Ошибка SMTP: {str(e)}"
        except Exception as e:
            logger.error(f"Connection error: {e}", exc_info=True)
            return False, f"Ошибка подключения: {str(e)}"
    
    @staticmethod
    def get_smtp_config(provider: str) -> dict:
        """Получение SMTP конфигурации по провайдеру"""
        return ManagerEmailService.SMTP_CONFIGS.get(
            provider.lower(),
            ManagerEmailService.SMTP_CONFIGS["yandex"]
        )

