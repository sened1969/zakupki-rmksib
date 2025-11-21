from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_button() -> list:
    """Кнопка возврата в главное меню"""
    return [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")]

def get_preferences_menu():
    """Главное меню настроек"""
    keyboard = [
        [InlineKeyboardButton(text="📧 Настройка Email", callback_data="pref:email")],
        [InlineKeyboardButton(text="🏷 Номенклатура", callback_data="pref:nom")],
        [InlineKeyboardButton(text="🏢 Заказчики", callback_data="pref:cust")],
        [InlineKeyboardButton(text="💰 Бюджет закупки", callback_data="pref:budget")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="pref:notify")],
        [InlineKeyboardButton(text="🔄 Запрос закупок", callback_data="pref:fetch_lots")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_customer_selection(selected: list | None = None):
    """Клавиатура выбора заказчиков"""
    from config.customers import CUSTOMERS_LIST
    selected = set(selected or [])
    keyboard = []
    
    # Используем индекс вместо полного названия для callback_data (ограничение Telegram: 64 байта)
    for idx, customer in enumerate(CUSTOMERS_LIST):
        status = "✅" if customer in selected else "⬜"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status} {customer}",
                callback_data=f"cust_t:{idx}"  # Используем индекс вместо полного названия
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="💾 Сохранить", callback_data="cust_save")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="pref:back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_nomenclature_selection(selected: list | None = None):
    """Клавиатура выбора номенклатуры"""
    from config.nomenclature import NOMENCLATURE_LIST
    selected = set(selected or [])
    keyboard = []
    
    # Разбиваем на группы по 2 кнопки в ряд для компактности
    # Используем индекс вместо полного названия для callback_data (ограничение Telegram: 64 байта)
    for i in range(0, len(NOMENCLATURE_LIST), 2):
        row = []
        for j in range(2):
            if i + j < len(NOMENCLATURE_LIST):
                idx = i + j
                nom = NOMENCLATURE_LIST[idx]
                status = "✅" if nom in selected else "⬜"
                # Показываем полное название в тексте, но используем индекс в callback_data
                display_text = f"{status} {nom[:25]}" if len(nom) > 25 else f"{status} {nom}"
                row.append(InlineKeyboardButton(
                    text=display_text,
                    callback_data=f"nom_t:{idx}"  # Используем индекс вместо полного названия
                ))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(text="💾 Сохранить", callback_data="nom_save")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="pref:back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_notify_toggle(enabled: bool):
    """Клавиатура переключения уведомлений"""
    keyboard = [
        [InlineKeyboardButton(
            text="✅ Включить" if not enabled else "❌ Выключить",
            callback_data=f"notify_toggle:{not enabled}"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="pref:back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_email_setup_menu():
    """Меню настройки email"""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Ввести Email", callback_data="email:set_email")],
        [InlineKeyboardButton(text="🔑 Ввести пароль", callback_data="email:set_password")],
        [InlineKeyboardButton(text="📮 Выбрать провайдер", callback_data="email:set_provider")],
        [InlineKeyboardButton(text="🧪 Проверить подключение", callback_data="email:test")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="pref:back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_smtp_provider_menu():
    """Меню выбора SMTP провайдера"""
    keyboard = [
        [InlineKeyboardButton(text="📧 Yandex", callback_data="smtp:yandex")],
        [InlineKeyboardButton(text="📧 Gmail", callback_data="smtp:gmail")],
        [InlineKeyboardButton(text="📧 Mail.ru", callback_data="smtp:mailru")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="pref:email")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_supplier_search_menu():
    keyboard = [
        [InlineKeyboardButton(text="Web-поиск", callback_data="search:perplexity")],
        [InlineKeyboardButton(text="Sniper Search", callback_data="search:sniper")],
        [InlineKeyboardButton(text="Назад", callback_data="search:back")]  # Кнопка "Назад"
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_search_input_menu():
    keyboard = [
        [InlineKeyboardButton(text="Ручной ввод", callback_data="input:manual")],
        [InlineKeyboardButton(text="Загрузить документ", callback_data="input:upload")],
        [InlineKeyboardButton(text="Назад", callback_data="input:back")]  # Добавленная кнопка «Назад»
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_after_search_menu():
    """Клавиатура после получения результатов поиска поставщиков"""
    keyboard = [
        [InlineKeyboardButton(text="📝 Сформировать запрос КП", callback_data="rfq:create")],
        [InlineKeyboardButton(text="✅ Завершить поиск", callback_data="rfq:finish")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_rfq_actions_menu():
    """Клавиатура для действий с запросом КП"""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Редактировать запрос", callback_data="rfq:edit")],
        [InlineKeyboardButton(text="📧 Сделать рассылку", callback_data="rfq:send")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="rfq:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_rfq_confirm_menu():
    """Клавиатура для подтверждения отправки"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Подтвердить отправку", callback_data="rfq:confirm_send")],
        [InlineKeyboardButton(text="✏️ Вернуться к редактированию", callback_data="rfq:edit")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="rfq:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_customer_fetch_menu():
    """Меню для запроса закупок по заказчикам"""
    from config.customers import CUSTOMERS_LIST, get_customer_info
    
    keyboard = []
    
    # Создаем кнопки для каждого заказчика
    # Используем индекс для callback_data (ограничение Telegram: 64 байта)
    for idx, customer in enumerate(CUSTOMERS_LIST):
        customer_info = get_customer_info(customer)
        parser_type = customer_info.get("parser_type")
        is_active = customer_info.get("is_active", False)
        
        # Определяем иконку статуса парсера
        if parser_type and is_active:
            icon = "✅"  # Парсер настроен и активен
        else:
            icon = "⚠️"  # Парсер не настроен
        
        # Обрезаем длинные названия для кнопки
        display_name = customer[:30] + "..." if len(customer) > 30 else customer
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} {display_name}",
                callback_data=f"fetch_cust:{idx}"  # Используем индекс
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="pref:back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_lots_pagination_keyboard(
    lots: list,
    current_page: int = 1,
    page_size: int = 10,
    callback_prefix: str = "lots:view:",
    page_callback_prefix: str = "lots:page:",
    show_add_doc_button: bool = True
) -> InlineKeyboardMarkup:
    """Создает клавиатуру с пагинацией для списка лотов"""
    from bot.keyboards.inline import get_main_menu_button
    
    total_lots = len(lots)
    total_pages = (total_lots + page_size - 1) // page_size if total_lots > 0 else 1
    
    # Ограничиваем текущую страницу
    current_page = max(1, min(current_page, total_pages))
    
    # Вычисляем индексы для текущей страницы
    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    page_lots = lots[start_idx:end_idx]
    
    keyboard = []
    
    # Кнопки лотов для текущей страницы
    for lot in page_lots:
        keyboard.append([InlineKeyboardButton(
            text=f"📋 {lot.lot_number}",
            callback_data=f"{callback_prefix}{lot.lot_number}"
        )])
    
    # Кнопки навигации по страницам
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"{page_callback_prefix}{current_page - 1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"📄 {current_page}/{total_pages}",
        callback_data="lots:page_info"
    ))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"{page_callback_prefix}{current_page + 1}"
        ))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Дополнительные кнопки
    if show_add_doc_button:
        keyboard.append([InlineKeyboardButton(text="📎 Добавить документацию", callback_data="lots:add_doc")])
    keyboard.append([InlineKeyboardButton(text="🔄 Запросить закупки", callback_data="pref:fetch_lots")])
    keyboard.append(get_main_menu_button())  # get_main_menu_button() уже возвращает список
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

