# Закупки РМКСИБ — AI-ассистент закупок (Telegram)

**Статус**: ✅ MVP готов к продакшену  
**Последнее обновление**: 25 ноября 2025

## Быстрый старт (Docker Compose)

1. Скопируйте `.env.example` в `.env` и заполните `BOT_TOKEN`.
2. Запустите: `docker compose up -d`.
3. Проверьте логи бота: `docker compose logs -f bot`.

## Локальный запуск (без Docker)

```bash
python -m venv .venv
# Windows PowerShell:
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # заполните BOT_TOKEN
python -m bot.main
```

## Основные функции

- ✅ Управление закупками (лоты, парсинг, фильтрация)
- ✅ AI-анализ лотов через Perplexity
- ✅ Email уведомления с фильтрацией
- ✅ Анализ коммерческих предложений (НОВОЕ)
- ✅ Статистика по лотам, КП, поставщикам, пользователям
- ✅ База поставщиков с рейтингами
- ✅ GUI-настройки пользователей
- ✅ **Django Admin Panel** для веб-управления данными (НОВОЕ)

## Структура

- `bot/` — вход, обработчики, клавиатуры, FSM, middleware
- `services/` — AI, парсеры, интеграции
- `database/` — модели и миграции (Alembic)
- `config/` — настройки и логирование
- `admin_panel/` — Django Admin Panel для веб-управления данными

## Документация

📚 **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** — полный индекс всей документации проекта

### Основные документы
- `PROJECT_STATUS.md` — полное описание проекта
- `QUICK_START.md` — инструкции по запуску
- `CURATOR_GUIDE.md` — руководство для куратора
- `ADMIN_PANEL_USER_GUIDE.md` — **инструкция по использованию админ-панели**
- `ADMIN_PANEL_SETUP.md` — настройка Django Admin Panel
- `admin_panel/README.md` — техническая документация Django Admin Panel

### Настройка и развертывание
- `RESOURCE_REQUIREMENTS.md` — требования к ресурсам
- `SNIPER_SEARCH_SETUP.md` — настройка Sniper Search API
- `GITHUB_DEPLOYMENT.md` — развертывание на GitHub
- `DOCKER_TROUBLESHOOTING.md` — решение проблем с Docker

## Требования к ресурсам

Для работы с нагрузкой (20 заявок/день, 200 КП, ~1000 товарных позиций):

**Минимальная конфигурация:**
- CPU: 2 ядра
- RAM: 2 ГБ
- Диск: 20 ГБ SSD

**Рекомендуемая конфигурация:**
- CPU: 4 ядра
- RAM: 4-8 ГБ
- Диск: 100 ГБ SSD

См. `RESOURCE_REQUIREMENTS.md` для детального анализа.

---

**Проект готов к продакшену. Все основные функции реализованы и протестированы.**
