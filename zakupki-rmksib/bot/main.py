import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config.settings import settings
from bot.handlers import start, admin, lots, suppliers, statistics, preferences_gui, supplier_search, rfq, settings_advanced, commercial_proposals
from bot.handlers import settings as settings_handler
from bot.handlers import unknown
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.logging import LoggingMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services import run_parsers_once
from services.parsers.job import cleanup_expired_lots

async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Проверка обязательных параметров
    if not settings.BOT_TOKEN:
        logging.error("BOT_TOKEN не установлен! Установите его в файле .env")
        raise ValueError("BOT_TOKEN is required. Please set it in .env file")

    # Примечание: БД инициализируется через Alembic миграции при запуске Docker
    # Для локального запуска: alembic upgrade head

    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем middleware на уровне message для правильной передачи данных
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(LoggingMiddleware())
    
    # Также регистрируем для callback queries
    dp.callback_query.middleware(AuthMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    # Регистрируем роутеры в правильном порядке
    # Сначала базовые обработчики сообщений БЕЗ FSM состояний
    dp.include_router(start.router)
    dp.include_router(admin.router)
    # Статистика регистрируем раньше, чтобы не перехватывалась обработчиками с FSM состояниями
    dp.include_router(statistics.router)
    # Обработчики настроек БЕЗ FSM - регистрируем ДО обработчиков с FSM
    dp.include_router(settings_handler.router)
    dp.include_router(preferences_gui.router)
    dp.include_router(settings_advanced.router)
    # Затем обработчики с FSM состояниями (могут перехватывать сообщения)
    dp.include_router(lots.router)
    dp.include_router(suppliers.router)
    # Обработчики коммерческих предложений (с FSM состояниями)
    dp.include_router(commercial_proposals.router)
    # Затем обработчики поиска и RFQ (также с FSM)
    dp.include_router(supplier_search.router)
    dp.include_router(rfq.router)
    # Обработчик неизвестных сообщений - должен быть последним
    dp.include_router(unknown.router)

    # Scheduler для периодических парсингов и очистки
    scheduler = AsyncIOScheduler()
    
    # Парсинг лотов (каждые N минут, если настроено)
    parser_interval = getattr(settings, 'PARSER_INTERVAL_MINUTES', 720)  # По умолчанию 12 часов
    if parser_interval > 0:
        scheduler.add_job(
            run_parsers_once, 
            "interval", 
            minutes=parser_interval, 
            id="parser-job", 
            replace_existing=True
        )
    
    # Очистка лотов с истекающим дедлайном (каждый день в 3:00)
    scheduler.add_job(
        cleanup_expired_lots,
        "cron",
        hour=3,
        minute=0,
        id="cleanup-expired-lots",
        replace_existing=True
    )
    
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
