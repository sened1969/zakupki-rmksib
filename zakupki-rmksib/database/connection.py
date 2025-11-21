from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings

# Формируем URL подключения к БД
# Если DATABASE_URL не указан, собираем из компонентов PostgreSQL
if settings.DATABASE_URL:
    database_url = settings.DATABASE_URL
    # Если это SQLite, добавляем aiosqlite драйвер
    if database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    # Если это PostgreSQL без asyncpg, заменяем на asyncpg
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
else:
    # Собираем URL из компонентов PostgreSQL
    if all([settings.POSTGRES_HOST, settings.POSTGRES_DB, settings.POSTGRES_USER, settings.POSTGRES_PASSWORD]):
        database_url = (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
    else:
        # Fallback на SQLite по умолчанию
        database_url = "sqlite+aiosqlite:///procurement.db"

# Создаём async engine
engine = create_async_engine(
    database_url,
    echo=False
)

# Создаём фабрику async сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    """Получить async сессию БД"""
    async with async_session_maker() as session:
        yield session

async def init_db():
    """Инициализировать БД"""
    pass
