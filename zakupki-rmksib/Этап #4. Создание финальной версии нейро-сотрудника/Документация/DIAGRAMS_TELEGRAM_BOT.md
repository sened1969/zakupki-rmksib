# Диаграммы архитектуры Telegram-бота "Закупки РМКСИБ"

## 1. Архитектурная диаграмма системы

```mermaid
graph TB
    subgraph "Telegram API"
        TG[Telegram Bot API]
    end
    
    subgraph "Bot Application"
        MAIN[bot/main.py<br/>Main Entry Point]
        DP[Dispatcher<br/>FSM Storage]
        
        subgraph "Middlewares"
            AUTH[AuthMiddleware<br/>Проверка доступа]
            LOG[LoggingMiddleware<br/>Логирование]
        end
        
        subgraph "Handlers"
            START[start.py<br/>Старт бота]
            ADMIN[admin.py<br/>Админ панель]
            LOTS[lots.py<br/>Управление лотами]
            SUPPLIERS[suppliers.py<br/>Поставщики]
            SEARCH[supplier_search.py<br/>Поиск поставщиков]
            RFQ[rfq.py<br/>Запросы КП]
            STATS[statistics.py<br/>Статистика]
            SETTINGS[settings.py<br/>Настройки]
            CP[commercial_proposals.py<br/>Коммерческие предложения]
            UNKNOWN[unknown.py<br/>Неизвестные команды]
        end
        
        subgraph "Keyboards"
            REPLY[reply.py<br/>Клавиатуры ответов]
            INLINE[inline.py<br/>Inline кнопки]
        end
        
        subgraph "States"
            FSM[forms.py<br/>FSM состояния]
        end
    end
    
    subgraph "Services Layer"
        subgraph "AI Services"
            PERPLEXITY[perplexity.py<br/>Perplexity AI]
            CP_ANALYSIS[commercial_proposal_analysis.py<br/>Анализ КП]
        end
        
        subgraph "Data Services"
            PARSER[parsers/<br/>Парсинг закупок]
            DOC[documentation/<br/>Обработка документов]
            EMAIL[email/<br/>Email уведомления]
            SEARCH_SVC[search/<br/>Поиск поставщиков]
        end
    end
    
    subgraph "Database Layer"
        DB[(PostgreSQL<br/>База данных)]
        subgraph "Repositories"
            USER_REPO[UserRepository]
            LOT_REPO[LotRepository]
            PREF_REPO[UserPreferenceRepository]
            SUPPLIER_REPO[SupplierRepository]
        end
    end
    
    subgraph "External APIs"
        PERPLEXITY_API[Perplexity API]
        SNIPER_API[Sniper Search API]
        SMTP[SMTP Server]
    end
    
    subgraph "Scheduler"
        SCHED[APScheduler<br/>Периодические задачи]
        PARSE_JOB[Парсинг лотов<br/>Каждые N минут]
        CLEANUP[Очистка истекших лотов<br/>Ежедневно в 3:00]
    end
    
    TG -->|Webhook/Polling| MAIN
    MAIN --> DP
    DP --> AUTH
    AUTH --> LOG
    LOG --> START
    LOG --> ADMIN
    LOG --> LOTS
    LOG --> SUPPLIERS
    LOG --> SEARCH
    LOG --> RFQ
    LOG --> STATS
    LOG --> SETTINGS
    LOG --> CP
    LOG --> UNKNOWN
    
    START --> REPLY
    LOTS --> INLINE
    SEARCH --> INLINE
    RFQ --> INLINE
    
    LOTS --> FSM
    SEARCH --> FSM
    RFQ --> FSM
    
    LOTS --> PERPLEXITY
    LOTS --> DOC
    LOTS --> EMAIL
    SEARCH --> PERPLEXITY
    SEARCH --> SEARCH_SVC
    CP --> CP_ANALYSIS
    
    PERPLEXITY --> PERPLEXITY_API
    SEARCH_SVC --> SNIPER_API
    EMAIL --> SMTP
    
    LOTS --> LOT_REPO
    START --> USER_REPO
    SETTINGS --> PREF_REPO
    SUPPLIERS --> SUPPLIER_REPO
    
    USER_REPO --> DB
    LOT_REPO --> DB
    PREF_REPO --> DB
    SUPPLIER_REPO --> DB
    
    MAIN --> SCHED
    SCHED --> PARSER
    SCHED --> CLEANUP
    PARSER --> LOT_REPO
    
    style MAIN fill:#e1f5ff
    style DP fill:#fff4e1
    style DB fill:#ffe1f5
    style PERPLEXITY_API fill:#e1ffe1
    style SNIPER_API fill:#e1ffe1
    style SMTP fill:#e1ffe1
```

## 2. Диаграмма последовательности: Анализ лота

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant Bot as Telegram Bot
    participant Handler as lots.py Handler
    participant DB as Database
    participant AI as Perplexity Service
    participant Doc as Documentation Service
    participant Email as Email Service
    
    User->>Bot: Нажимает "📋 Мои лоты"
    Bot->>Handler: show_my_lots()
    Handler->>DB: Получить настройки пользователя
    DB-->>Handler: UserPreferences
    Handler->>DB: Получить все лоты
    DB-->>Handler: List[Lot]
    Handler->>Handler: Фильтрация по настройкам
    Handler-->>Bot: Отправить список лотов
    Bot-->>User: Показать список лотов
    
    User->>Bot: Выбирает лот (callback)
    Bot->>Handler: show_lot_detail()
    Handler->>DB: Получить детали лота
    DB-->>Handler: Lot object
    Handler-->>Bot: Отправить детали лота
    Bot-->>User: Показать детали лота
    
    User->>Bot: Нажимает "🧠 Анализ лота"
    Bot->>Handler: analyze_lot_callback()
    Handler->>DB: Проверить наличие документации
    DB-->>Handler: Documentation status
    
    alt Документация есть
        Handler->>Doc: Извлечь текст из документации
        Doc-->>Handler: Text content
        Handler->>AI: analyze_lot_enhanced(lot, doc_text)
    else Документации нет
        Handler->>AI: analyze_lot_basic(lot)
    end
    
    AI->>AI: Формирование промпта
    AI->>AI: Вызов Perplexity API
    AI-->>Handler: AI анализ
    Handler->>DB: Сохранить анализ
    Handler-->>Bot: Отправить результат анализа
    Bot-->>User: Показать анализ лота
    
    opt Отправка на email
        User->>Bot: Нажимает "📧 Отправить на email"
        Bot->>Handler: send_analysis_email()
        Handler->>DB: Получить email настройки
        DB-->>Handler: Email settings
        Handler->>Email: Отправить email с анализом
        Email-->>Handler: Email отправлен
        Handler-->>Bot: Подтверждение
        Bot-->>User: ✅ Email отправлен
    end
```

## 3. Диаграмма последовательности: Поиск поставщиков

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant Bot as Telegram Bot
    participant Handler as supplier_search.py
    participant FSM as FSM State Machine
    participant AI as Perplexity Service
    participant Sniper as Sniper Search Service
    participant DB as Database
    
    User->>Bot: Нажимает "🔍 Поиск Поставщиков"
    Bot->>Handler: supplier_search_start()
    Handler->>FSM: set_state(choosing_method)
    Handler-->>Bot: Показать меню выбора метода
    Bot-->>User: Выберите метод поиска
    
    User->>Bot: Выбирает метод (Perplexity/Sniper)
    Bot->>Handler: process_search_method()
    Handler->>FSM: update_data(search_method)
    Handler->>FSM: set_state(choosing_input)
    Handler-->>Bot: Показать меню ввода данных
    Bot-->>User: Как ввести данные?
    
    User->>Bot: Выбирает способ ввода
    Bot->>Handler: process_input_method()
    
    alt Ручной ввод
        Handler->>FSM: set_state(manual_input)
        Handler-->>Bot: Запросить название товара
        Bot-->>User: Введите название товара
        User->>Bot: Вводит название товара
        Bot->>Handler: process_manual_input()
        Handler->>FSM: update_data(product_name)
    else Загрузка документа
        Handler->>FSM: set_state(waiting_document)
        Handler-->>Bot: Запросить документ
        Bot-->>User: Загрузите документ
        User->>Bot: Отправляет документ
        Bot->>Handler: process_document()
        Handler->>Doc: Извлечь текст
        Doc-->>Handler: Text content
        Handler->>AI: Анализ документа
        AI-->>Handler: Product names
        Handler->>FSM: update_data(product_name)
    end
    
    Handler->>FSM: set_state(processing)
    Handler-->>Bot: Показать "Обработка..."
    Bot-->>User: ⏳ Обработка запроса
    
    alt Метод: Perplexity
        Handler->>AI: search_suppliers_perplexity(product_name)
        AI->>AI: Формирование промпта
        AI->>AI: Вызов Perplexity API
        AI-->>Handler: Список поставщиков
    else Метод: Sniper Search
        Handler->>Sniper: search_suppliers(product_name)
        Sniper->>Sniper: Вызов Sniper API
        Sniper-->>Handler: Список поставщиков
    end
    
    Handler->>DB: Сохранить результаты поиска
    Handler->>FSM: clear()
    Handler-->>Bot: Отправить результаты
    Bot-->>User: Показать список поставщиков
```

## 4. Диаграмма состояний (FSM) бота

```mermaid
stateDiagram-v2
    [*] --> Idle: Бот запущен
    
    Idle --> StartMenu: /start или "🚀 Старт"
    StartMenu --> MyLots: "📋 Мои лоты"
    StartMenu --> SupplierSearch: "🔍 Поиск Поставщиков"
    StartMenu --> Settings: "⚙️ Настройки"
    StartMenu --> Statistics: "📊 Статистика"
    StartMenu --> AdminPanel: "👑 Админ панель" (если admin)
    
    state "Работа с лотами" as LotsFlow {
        MyLots --> LotDetail: Выбор лота
        LotDetail --> LotAnalysis: "🧠 Анализ лота"
        LotDetail --> UploadDoc: "📎 Загрузить документацию"
        LotDetail --> DownloadDoc: "📥 Скачать документацию"
        LotDetail --> SearchSupplier: "🔍 Поиск Поставщиков"
        UploadDoc --> DocumentationStates: Ожидание документа
        DocumentationStates --> LotDetail: Документ загружен
        LotAnalysis --> EmailAnalysis: "📧 Отправить на email"
        EmailAnalysis --> LotDetail: Email отправлен
        SearchSupplier --> SupplierSearchFlow
    }
    
    state "Поиск поставщиков" as SupplierSearchFlow {
        [*] --> ChoosingMethod: Начало поиска
        ChoosingMethod --> ChoosingInput: Выбор метода
        ChoosingInput --> ManualInput: Ручной ввод
        ChoosingInput --> WaitingDocument: Загрузка документа
        ManualInput --> Processing: Ввод завершен
        WaitingDocument --> Processing: Документ обработан
        Processing --> ViewingResults: Результаты готовы
        ViewingResults --> [*]: Поиск завершен
    }
    
    state "Настройки" as SettingsFlow {
        [*] --> SettingsMenu: Меню настроек
        SettingsMenu --> CustomerSettings: Настройка заказчиков
        SettingsMenu --> NomenclatureSettings: Настройка номенклатуры
        SettingsMenu --> BudgetSettings: Настройка бюджета
        SettingsMenu --> EmailSettings: Настройка email
        CustomerSettings --> SettingsMenu: Сохранено
        NomenclatureSettings --> SettingsMenu: Сохранено
        BudgetSettings --> SettingsMenu: Сохранено
        EmailSettings --> SettingsMenu: Сохранено
    }
    
    state "RFQ (Запрос КП)" as RFQFlow {
        [*] --> ViewingRFQDraft: Просмотр черновика
        ViewingRFQDraft --> EditingRFQText: Редактирование текста
        EditingRFQText --> ConfirmingSend: Подтверждение отправки
        ConfirmingSend --> [*]: RFQ отправлен
    }
    
    state "Коммерческие предложения" as CPFlow {
        [*] --> SelectingAction: Выбор действия
        SelectingAction --> UploadingProposal: Загрузка КП
        SelectingAction --> GeneratingReport: Формирование отчета
        UploadingProposal --> EnteringSupplierName: Ввод данных поставщика
        EnteringSupplierName --> EnteringSupplierINN: Ввод ИНН
        EnteringSupplierINN --> EnteringProductPrice: Ввод цены
        EnteringProductPrice --> EnteringDeliveryCost: Ввод доставки
        EnteringDeliveryCost --> EnteringOtherConditions: Прочие условия
        EnteringOtherConditions --> ConfirmingProposal: Подтверждение
        ConfirmingProposal --> [*]: КП сохранено
    }
    
    MyLots --> LotsFlow
    SupplierSearch --> SupplierSearchFlow
    Settings --> SettingsFlow
    LotDetail --> RFQFlow: Формирование RFQ
    LotDetail --> CPFlow: Работа с КП
    
    LotsFlow --> StartMenu: "🔙 Назад"
    SupplierSearchFlow --> StartMenu: "🔙 Назад"
    SettingsFlow --> StartMenu: "🔙 Назад"
    RFQFlow --> StartMenu: "🔙 Назад"
    CPFlow --> StartMenu: "🔙 Назад"
    
    StartMenu --> Idle: Выход
```

## 5. Диаграмма классов основных компонентов

```mermaid
classDiagram
    class Bot {
        +Bot(token: str)
        +send_message()
        +edit_message()
        +answer_callback()
    }
    
    class Dispatcher {
        +storage: MemoryStorage
        +include_router()
        +start_polling()
    }
    
    class AuthMiddleware {
        +__call__(event, data)
        -get_or_create_user()
    }
    
    class LoggingMiddleware {
        +__call__(handler, event, data)
        -log_update()
    }
    
    class StartHandler {
        +start()
        +start_button_handler()
    }
    
    class LotsHandler {
        +show_my_lots()
        +show_lot_detail()
        +analyze_lot_callback()
        +upload_documentation()
        +send_analysis_email()
        -_lot_matches_preferences()
    }
    
    class SupplierSearchHandler {
        +supplier_search_start()
        +process_search_method()
        +process_input_method()
        +process_manual_input()
        +process_document()
    }
    
    class UserRepository {
        +get_or_create_by_telegram_id()
        +update_last_seen()
        +get_by_id()
    }
    
    class LotRepository {
        +get_all()
        +get_by_lot_number()
        +create()
        +update()
    }
    
    class UserPreferenceRepository {
        +get_or_create()
        +update_customers()
        +update_nomenclature()
        +update_budget()
    }
    
    class PerplexityService {
        +ask_perplexity()
        +analyze_lot_basic()
        +analyze_lot_enhanced()
        +search_suppliers_perplexity()
    }
    
    class SniperSearchService {
        +search_suppliers()
        +__aenter__()
        +__aexit__()
    }
    
    class DocumentationService {
        +save_documentation_file()
        +extract_text_from_file()
        +is_supported_format()
        +download_documentation_from_url()
    }
    
    class EmailService {
        +send_email()
        +send_analysis_email()
        +format_email_content()
    }
    
    class User {
        +id: int
        +telegram_id: int
        +username: str
        +full_name: str
        +role: str
        +created_at: datetime
        +last_seen: datetime
    }
    
    class Lot {
        +id: int
        +lot_number: str
        +title: str
        +customer: str
        +budget: float
        +deadline: datetime
        +url: str
    }
    
    class UserPreference {
        +id: int
        +user_id: int
        +customers: list
        +nomenclature: list
        +budget_min: float
        +budget_max: float
        +email: str
    }
    
    Bot --> Dispatcher
    Dispatcher --> AuthMiddleware
    Dispatcher --> LoggingMiddleware
    Dispatcher --> StartHandler
    Dispatcher --> LotsHandler
    Dispatcher --> SupplierSearchHandler
    
    LotsHandler --> LotRepository
    LotsHandler --> UserPreferenceRepository
    LotsHandler --> PerplexityService
    LotsHandler --> DocumentationService
    LotsHandler --> EmailService
    
    SupplierSearchHandler --> PerplexityService
    SupplierSearchHandler --> SniperSearchService
    SupplierSearchHandler --> DocumentationService
    
    AuthMiddleware --> UserRepository
    
    UserRepository --> User
    LotRepository --> Lot
    UserPreferenceRepository --> UserPreference
    
    UserPreference --> User
```

## 6. Диаграмма потока данных: Обработка сообщения пользователя

```mermaid
flowchart TD
    Start([Пользователь отправляет сообщение]) --> TG[Telegram API]
    TG --> Bot[Bot Instance]
    Bot --> Dispatcher[Dispatcher]
    
    Dispatcher --> AuthMW[AuthMiddleware]
    AuthMW --> CheckUser{Пользователь<br/>в БД?}
    CheckUser -->|Нет| CreateUser[Создать пользователя]
    CheckUser -->|Да| UpdateSeen[Обновить last_seen]
    CreateUser --> UpdateSeen
    UpdateSeen --> LogMW[LoggingMiddleware]
    
    LogMW --> Route{Определить<br/>роутер}
    
    Route -->|/start| StartHandler[Start Handler]
    Route -->|📋 Мои лоты| LotsHandler[Lots Handler]
    Route -->|🔍 Поиск| SearchHandler[Search Handler]
    Route -->|⚙️ Настройки| SettingsHandler[Settings Handler]
    Route -->|👑 Админ| AdminHandler[Admin Handler]
    Route -->|Неизвестно| UnknownHandler[Unknown Handler]
    
    StartHandler --> MainMenu[Показать главное меню]
    
    LotsHandler --> CheckFSM{FSM<br/>состояние?}
    CheckFSM -->|Нет| GetLots[Получить лоты из БД]
    GetLots --> FilterLots[Фильтрация по настройкам]
    FilterLots --> ShowLots[Показать список лотов]
    
    CheckFSM -->|Да| ProcessState[Обработать состояние]
    ProcessState --> UploadDoc{Загрузка<br/>документа?}
    UploadDoc -->|Да| SaveDoc[Сохранить документ]
    SaveDoc --> ExtractText[Извлечь текст]
    ExtractText --> ProcessState
    
    LotsHandler --> AnalyzeLot{Анализ<br/>лота?}
    AnalyzeLot -->|Да| CheckDoc{Есть<br/>документация?}
    CheckDoc -->|Да| AIEnhanced[AI анализ с документацией]
    CheckDoc -->|Нет| AIBasic[AI базовый анализ]
    AIEnhanced --> PerplexityAPI[Perplexity API]
    AIBasic --> PerplexityAPI
    PerplexityAPI --> SaveAnalysis[Сохранить анализ]
    SaveAnalysis --> ShowAnalysis[Показать анализ]
    
    SearchHandler --> CheckMethod{Метод<br/>поиска?}
    CheckMethod -->|Perplexity| PerplexitySearch[Perplexity Search]
    CheckMethod -->|Sniper| SniperSearch[Sniper Search]
    PerplexitySearch --> PerplexityAPI
    SniperSearch --> SniperAPI[Sniper Search API]
    PerplexityAPI --> ShowResults[Показать результаты]
    SniperAPI --> ShowResults
    
    SettingsHandler --> UpdatePrefs[Обновить настройки]
    UpdatePrefs --> SavePrefs[Сохранить в БД]
    
    AdminHandler --> CheckRole{Роль<br/>admin?}
    CheckRole -->|Да| AdminActions[Админ действия]
    CheckRole -->|Нет| AccessDenied[Доступ запрещен]
    
    MainMenu --> Response[Отправить ответ]
    ShowLots --> Response
    ShowAnalysis --> Response
    ShowResults --> Response
    SavePrefs --> Response
    AdminActions --> Response
    AccessDenied --> Response
    UnknownHandler --> Response
    
    Response --> End([Завершение обработки])
    
    style Start fill:#e1f5ff
    style End fill:#ffe1f5
    style PerplexityAPI fill:#e1ffe1
    style SniperAPI fill:#e1ffe1
    style CheckFSM fill:#fff4e1
    style CheckMethod fill:#fff4e1
```

## 7. Диаграмма компонентов системы

```mermaid
graph LR
    subgraph "Presentation Layer"
        TG[Telegram Bot Interface]
    end
    
    subgraph "Application Layer"
        HANDLERS[Handlers<br/>Обработчики команд]
        MIDDLEWARES[Middlewares<br/>Промежуточное ПО]
        KEYBOARDS[Keyboards<br/>Клавиатуры]
        STATES[FSM States<br/>Состояния]
    end
    
    subgraph "Business Logic Layer"
        AI_SVC[AI Services<br/>AI сервисы]
        DOC_SVC[Document Services<br/>Обработка документов]
        EMAIL_SVC[Email Services<br/>Email уведомления]
        SEARCH_SVC[Search Services<br/>Поиск поставщиков]
        PARSER_SVC[Parser Services<br/>Парсинг закупок]
    end
    
    subgraph "Data Access Layer"
        REPOS[Repositories<br/>Репозитории данных]
        MODELS[Models<br/>Модели данных]
    end
    
    subgraph "Infrastructure Layer"
        DB[(PostgreSQL<br/>База данных)]
        REDIS[(Redis<br/>Кэш)]
        SCHEDULER[Scheduler<br/>Планировщик задач]
    end
    
    subgraph "External Services"
        PERPLEXITY[Perplexity AI API]
        SNIPER[Sniper Search API]
        SMTP[SMTP Server]
        TG_API[Telegram API]
    end
    
    TG --> TG_API
    TG_API --> HANDLERS
    HANDLERS --> MIDDLEWARES
    HANDLERS --> KEYBOARDS
    HANDLERS --> STATES
    
    HANDLERS --> AI_SVC
    HANDLERS --> DOC_SVC
    HANDLERS --> EMAIL_SVC
    HANDLERS --> SEARCH_SVC
    HANDLERS --> PARSER_SVC
    
    HANDLERS --> REPOS
    REPOS --> MODELS
    MODELS --> DB
    
    AI_SVC --> PERPLEXITY
    SEARCH_SVC --> SNIPER
    EMAIL_SVC --> SMTP
    
    SCHEDULER --> PARSER_SVC
    SCHEDULER --> REPOS
    
    style TG fill:#e1f5ff
    style DB fill:#ffe1f5
    style PERPLEXITY fill:#e1ffe1
    style SNIPER fill:#e1ffe1
    style SMTP fill:#e1ffe1
```

## 8. Диаграмма развертывания

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Docker Container: Bot"
            BOT_APP[bot/main.py<br/>Python Application]
            BOT_DEPS[aiogram, apscheduler<br/>Dependencies]
        end
        
        subgraph "Docker Container: Database"
            POSTGRES[(PostgreSQL<br/>Database)]
            ALEMBIC[Alembic<br/>Migrations]
        end
        
        subgraph "Docker Container: Redis"
            REDIS[(Redis<br/>Cache & Storage)]
        end
        
        subgraph "External Services"
            PERPLEXITY_API[Perplexity AI API<br/>https://api.perplexity.ai]
            SNIPER_API[Sniper Search API<br/>https://api.sniper-search.com]
            SMTP_SERVER[SMTP Server<br/>Email Service]
            TG_API[Telegram Bot API<br/>https://api.telegram.org]
        end
        
        subgraph "Configuration"
            ENV_FILE[.env<br/>Environment Variables]
            DOCKER_COMPOSE[docker-compose.yml<br/>Orchestration]
        end
    end
    
    subgraph "Scheduled Tasks"
        PARSER_JOB[Parser Job<br/>Every N minutes]
        CLEANUP_JOB[Cleanup Job<br/>Daily at 3:00 AM]
    end
    
    ENV_FILE --> BOT_APP
    DOCKER_COMPOSE --> BOT_APP
    DOCKER_COMPOSE --> POSTGRES
    DOCKER_COMPOSE --> REDIS
    
    BOT_APP --> BOT_DEPS
    BOT_APP --> POSTGRES
    BOT_APP --> REDIS
    BOT_APP --> TG_API
    BOT_APP --> PERPLEXITY_API
    BOT_APP --> SNIPER_API
    BOT_APP --> SMTP_SERVER
    
    ALEMBIC --> POSTGRES
    
    PARSER_JOB --> BOT_APP
    CLEANUP_JOB --> BOT_APP
    
    style BOT_APP fill:#e1f5ff
    style POSTGRES fill:#ffe1f5
    style PERPLEXITY_API fill:#e1ffe1
    style SNIPER_API fill:#e1ffe1
    style SMTP_SERVER fill:#e1ffe1
    style TG_API fill:#e1ffe1
```

## Описание диаграмм

### 1. Архитектурная диаграмма системы
Показывает общую структуру бота, взаимодействие компонентов, middleware, handlers, services и внешние API.

### 2. Диаграмма последовательности: Анализ лота
Детализирует процесс анализа лота от запроса пользователя до получения результата и отправки на email.

### 3. Диаграмма последовательности: Поиск поставщиков
Показывает полный цикл поиска поставщиков с использованием FSM состояний и различных методов поиска.

### 4. Диаграмма состояний (FSM)
Визуализирует все возможные состояния бота и переходы между ними при работе с различными функциями.

### 5. Диаграмма классов
Отображает основные классы системы, их методы и взаимосвязи между компонентами.

### 6. Диаграмма потока данных
Показывает поток обработки сообщения пользователя от получения до отправки ответа.

### 7. Диаграмма компонентов системы
Демонстрирует слоистую архитектуру приложения с разделением на Presentation, Application, Business Logic, Data Access и Infrastructure слои.

### 8. Диаграмма развертывания
Показывает инфраструктуру развертывания бота в Docker контейнерах и взаимодействие с внешними сервисами.

