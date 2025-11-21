from datetime import datetime

def format_rub(amount: float | int) -> str:
    """Форматирует сумму в рублях"""
    return f"{amount:,.0f} ₽".replace(",", " ")


def format_date(dt: datetime) -> str:
    return dt.strftime('%d.%m.%Y')


def format_separator(length: int = 25) -> str:
    """Создает визуальный разделитель"""
    return "━" * length


def format_number(value: int | float) -> str:
    """Форматирует число с моноширинным шрифтом"""
    if isinstance(value, float):
        return f"<code>{value:,.1f}</code>".replace(",", " ")
    return f"<code>{value:,}</code>".replace(",", " ")
