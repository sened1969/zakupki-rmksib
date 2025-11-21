import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    REDIS_URL = os.getenv('REDIS_URL')
    DATABASE_URL = os.getenv('DATABASE_URL')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')
    PERPLEXITY_MODEL = os.getenv('PERPLEXITY_MODEL', 'sonar')  # sonar, sonar-pro, llama-3.1-sonar-small-32k-online, llama-3.1-sonar-large-32k-online
    SNIPER_SEARCH_BASE_URL = os.getenv('SNIPER_SEARCH_BASE_URL', 'https://api.sniper-search.com')
    SNIPER_SEARCH_API_TOKEN = os.getenv('SNIPER_SEARCH_API_TOKEN', '')  # API токен для Sniper Search
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', '')
    IMAP_HOST = os.getenv('IMAP_HOST', '')
    IMAP_PORT = int(os.getenv('IMAP_PORT', '993'))
    EMAIL_PASS = os.getenv('EMAIL_PASS', '')
    BUDGET_THRESHOLD_RUB = int(os.getenv('BUDGET_THRESHOLD_RUB', '3000000'))
    AI_OVERHEAD_PERCENT = int(os.getenv('AI_OVERHEAD_PERCENT', '15'))
    PARSER_INTERVAL_MINUTES = int(os.getenv('PARSER_INTERVAL_MINUTES', '30'))
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')  # Ключ для шифрования паролей (опционально)

def get_notify_emails():
    """Парсит NOTIFY_EMAILS из строки в список"""
    emails_str = os.getenv('NOTIFY_EMAILS', '')
    return [email.strip() for email in emails_str.split(',') if email.strip()]

settings = Settings()
settings.NOTIFY_EMAILS = get_notify_emails()
