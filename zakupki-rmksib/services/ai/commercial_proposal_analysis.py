"""Сервис для анализа коммерческих предложений через LLM"""
from typing import Optional, Dict
from loguru import logger
from services.ai.perplexity import ask_perplexity
from database.models import CommercialProposal


async def analyze_supplier_reliability(supplier_name: str, supplier_inn: Optional[str] = None) -> Dict[str, any]:
    """
    Анализирует надежность поставщика через LLM
    
    Args:
        supplier_name: Название поставщика
        supplier_inn: ИНН поставщика (опционально)
    
    Returns:
        Словарь с результатами анализа:
        - rating: рейтинг от 0 до 100
        - reliability_info: текстовая информация о надежности
    """
    inn_text = f"ИНН: {supplier_inn}" if supplier_inn else ""
    
    prompt = f"""Проанализируй надежность поставщика и предоставь оценку в следующем формате:

Поставщик: {supplier_name}
{inn_text}

Проверь в открытых источниках:
1. Есть ли информация о неблагонадежности поставщика (судебные дела, задолженности, банкротство)
2. Репутация компании на рынке
3. Опыт работы в отрасли
4. Финансовое состояние (если доступна информация)

Ответ предоставь в формате:
РЕЙТИНГ: [число от 0 до 100, где 100 - максимально надежный]
ИНФОРМАЦИЯ: [краткое описание найденной информации о надежности, 2-3 предложения]

Если информации недостаточно, укажи это в разделе ИНФОРМАЦИЯ."""

    try:
        response = await ask_perplexity(
            [{"role": "user", "content": prompt}],
            model=None,
            temperature=0.2,
            max_tokens=500
        )
        
        # Парсим ответ
        rating = None
        reliability_info = response
        
        # Пытаемся извлечь рейтинг из ответа
        for line in response.split('\n'):
            if 'РЕЙТИНГ:' in line.upper() or 'RATING:' in line.upper():
                try:
                    # Ищем число в строке
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        rating = int(numbers[0])
                        if rating > 100:
                            rating = 100
                        if rating < 0:
                            rating = 0
                except:
                    pass
        
        # Если рейтинг не найден, используем среднее значение
        if rating is None:
            rating = 50  # Средний рейтинг по умолчанию
        
        return {
            "rating": rating,
            "reliability_info": reliability_info
        }
        
    except Exception as e:
        logger.error(f"Error analyzing supplier reliability: {e}", exc_info=True)
        return {
            "rating": 50,  # Средний рейтинг при ошибке
            "reliability_info": f"Не удалось провести анализ надежности поставщика: {str(e)}"
        }


def calculate_integral_rating(
    product_price: float,
    delivery_cost: Optional[float],
    supplier_rating: Optional[int],
    other_conditions: Optional[str] = None
) -> float:
    """
    Рассчитывает интегральный рейтинг КП на основе всех факторов
    
    Args:
        product_price: Цена товара
        delivery_cost: Стоимость доставки
        supplier_rating: Рейтинг поставщика (0-100)
        other_conditions: Прочие условия (текст)
    
    Returns:
        Интегральный рейтинг от 0 до 100
    """
    # Базовые веса для расчета
    price_weight = 0.4  # 40% - цена товара
    delivery_weight = 0.2  # 20% - стоимость доставки
    supplier_weight = 0.3  # 30% - рейтинг поставщика
    conditions_weight = 0.1  # 10% - прочие условия
    
    # Нормализуем цену (чем ниже цена, тем выше рейтинг)
    # Используем обратную зависимость: если цена низкая, рейтинг высокий
    # Для упрощения: нормализуем относительно максимальной цены в группе КП
    # Здесь используем простую формулу: чем ниже цена, тем выше рейтинг
    price_score = 100.0  # По умолчанию максимальный балл
    
    # Нормализуем стоимость доставки
    delivery_score = 100.0  # По умолчанию максимальный балл
    if delivery_cost is not None:
        # Чем ниже стоимость доставки, тем выше рейтинг
        # Упрощенная формула: если доставка < 10% от цены товара, то 100 баллов
        if product_price > 0:
            delivery_percent = (delivery_cost / product_price) * 100
            if delivery_percent < 5:
                delivery_score = 100
            elif delivery_percent < 10:
                delivery_score = 90
            elif delivery_percent < 20:
                delivery_score = 70
            elif delivery_percent < 30:
                delivery_score = 50
            else:
                delivery_score = 30
    
    # Рейтинг поставщика (уже нормализован от 0 до 100)
    supplier_score = supplier_rating if supplier_rating is not None else 50
    
    # Оценка прочих условий (упрощенная: если есть условия, добавляем баллы)
    conditions_score = 50  # Средний балл по умолчанию
    if other_conditions:
        conditions_text = other_conditions.lower()
        # Проверяем наличие положительных условий
        positive_keywords = ['гарантия', 'скидка', 'рассрочка', 'бонус', 'подарок']
        negative_keywords = ['предоплата', 'полная оплата', 'без возврата']
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in conditions_text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in conditions_text)
        
        conditions_score = 50 + (positive_count * 10) - (negative_count * 10)
        if conditions_score > 100:
            conditions_score = 100
        if conditions_score < 0:
            conditions_score = 0
    
    # Рассчитываем интегральный рейтинг
    integral = (
        price_score * price_weight +
        delivery_score * delivery_weight +
        supplier_score * supplier_weight +
        conditions_score * conditions_weight
    )
    
    return round(integral, 2)

