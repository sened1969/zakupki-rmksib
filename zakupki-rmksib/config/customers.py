"""Справочник заказчиков"""
from typing import Dict

# Справочник заказчиков с их настройками парсинга
CUSTOMERS_CATALOG: Dict[str, Dict] = {
    "Селигдар": {
        "parser_type": None,  # Требуется настройка
        "is_active": False,
        "url": None
    },
    "ГРК «Быстринское» (Норильский Никель)": {
        "parser_type": None,
        "is_active": False,
        "url": None
    },
    "АО \"ПАВЛИК\"": {
        "parser_type": "pavlik_static",
        "is_active": True,  # АКТИВНЫЙ на тестовом этапе
        "url": "https://www.pavlik-gold.ru/suppliers/",
        "archive_url": "https://www.pavlik-gold.ru/suppliers/archive.php"
    },
    "Северсталь": {
        "parser_type": None,
        "is_active": False,
        "url": None
    },
    "Полиметалл": {
        "parser_type": None,
        "is_active": False,
        "url": None
    },
    "Полюс": {
        "parser_type": None,
        "is_active": False,
        "url": None
    },
    "Высочайший": {
        "parser_type": None,
        "is_active": False,
        "url": None
    },
    "Удоканская медь": {
        "parser_type": None,
        "is_active": False,
        "url": None
    },
    "Западная": {
        "parser_type": None,
        "is_active": False,
        "url": None
    }
}

# Список всех заказчиков
CUSTOMERS_LIST = list(CUSTOMERS_CATALOG.keys())


def get_customer_info(customer_name: str) -> Dict:
    """Получить информацию о заказчике"""
    return CUSTOMERS_CATALOG.get(customer_name, {})


def is_customer_active(customer_name: str) -> bool:
    """Проверить, активен ли парсер для заказчика"""
    info = get_customer_info(customer_name)
    return info.get("is_active", False)
















