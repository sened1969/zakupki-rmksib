"""Справочник номенклатурных групп"""
from typing import Dict, List, Optional
from loguru import logger

# Специальная позиция "Все лоты" - означает парсинг всех лотов без фильтрации по номенклатуре
ALL_LOTS_KEY = "Все лоты"

# Справочник номенклатурных групп с ключевыми словами для фильтрации
NOMENCLATURE_CATALOG: Dict[str, List[str]] = {
    "Строительные материалы": [
        "цемент", "бетон", "кирпич", "песок", "щебень", "гравий", "асфальт",
        "гипс", "известь", "штукатурка", "краска", "лак", "грунтовка"
    ],
    "Строительное оборудование": [
        "бетономешалка", "крановое", "леса", "строительное оборудование",
        "компрессор", "сварочное", "инструмент строительный"
    ],
    "Геосинтетические и геополимерные материалы и изделия": [
        "геосинтетика", "геотекстиль", "геомембрана", "геополимер",
        "георешетка", "геосетка"
    ],
    "Изделия для технологических трубопроводов": [
        "труба", "трубопровод", "арматура трубопроводная", "фланец",
        "задвижка", "кран", "клапан", "отвод", "тройник"
    ],
    "Электротехнические материалы и изделия": [
        "кабель", "провод", "электротехнический", "изоляция",
        "розетка", "выключатель", "автомат", "щит", "светильник"
    ],
    "Запасные части для спецтехники": [
        "запчасть", "деталь", "комплектующая", "фильтр", "масло",
        "гидравлика", "гидроцилиндр", "насос", "двигатель"
    ],
    "Промышленное оборудование": [
        "оборудование промышленное", "станок", "пресс", "насосное",
        "вентиляционное", "котельное", "насос"
    ],
    "Геодезическое и геологоразведочное оборудование": [
        "геодезия", "геологоразведка", "теодолит", "нивелир",
        "gps", "gnss", "тахеометр"
    ],
    "Контрольно-измерительные приборы": [
        "кип", "прибор", "датчик", "измерительный", "контрольный",
        "манометр", "термометр", "расходомер"
    ],
    "Спецхимия": [
        "химия", "реагент", "реактив", "кислота", "щелочь",
        "растворитель", "смазка", "антифриз"
    ],
    "Инструменты": [
        "инструмент", "ключ", "отвертка", "молоток", "дрель",
        "болгарка", "перфоратор", "пила"
    ],
    "Резинотехнические изделия": [
        "рти", "резина", "уплотнитель", "прокладка", "манжета",
        "шланг", "рукав", "лента конвейерная"
    ],
    "Метизы и крепёжные изделия": [
        "болт", "гайка", "винт", "шпилька", "шайба", "метиз",
        "крепеж", "анкер", "дюбель", "саморез", "гвоздь"
    ],
    "Мебель и системы хранения": [
        "мебель", "шкаф", "стол", "стул", "стеллаж", "полка",
        "система хранения", "ящик"
    ],
    "Спецодежда, СИЗ, товары для ОТ и ТБ": [
        "спецодежда", "сиз", "каска", "перчатка", "очки",
        "респиратор", "обувь рабочая", "костюм"
    ],
    "Компьютерная техника и периферия": [
        "компьютер", "ноутбук", "монитор", "принтер", "сканер",
        "клавиатура", "мышь", "сервер", "сетевое оборудование"
    ],
    "Бытовая техника": [
        "бытовая техника", "холодильник", "стиральная машина",
        "микроволновка", "чайник", "утюг"
    ],
    "Хозяйственные товары": [
        "хозяйственный", "моющее средство", "тряпка", "ведро",
        "швабра", "инвентарь хозяйственный"
    ],
    "Тара": [
        "тара", "контейнер", "ящик", "бочка", "канистра",
        "бидон", "мешок", "пакет"
    ],
    "Прочие ТМЦ": [
        "прочее", "тмц", "материал", "изделие"
    ],
    "Лабораторное оборудование": [
        "лабораторное", "весы", "аналитический", "микроскоп",
        "термостат", "сушильный шкаф"
    ]
}

# Список всех номенклатурных групп (с "Все лоты" в начале)
NOMENCLATURE_LIST = [ALL_LOTS_KEY] + list(NOMENCLATURE_CATALOG.keys())


def get_nomenclature_keywords(nomenclature_name: str) -> List[str]:
    """Получить ключевые слова для номенклатурной группы"""
    # Для "Все лоты" возвращаем пустой список (фильтрация не применяется)
    if nomenclature_name == ALL_LOTS_KEY:
        return []
    return NOMENCLATURE_CATALOG.get(nomenclature_name, [])


def check_nomenclature_match(lot_name: str, nomenclature_list: List[str]) -> bool:
    """
    Проверяет, соответствует ли название лота выбранным номенклатурным группам
    Использует простое сопоставление по ключевым словам.
    
    Args:
        lot_name: Название лота
        nomenclature_list: Список выбранных номенклатурных групп
    
    Returns:
        True если лот соответствует хотя бы одной номенклатурной группе
        Если в списке есть "Все лоты", всегда возвращает True
    """
    if not nomenclature_list:
        return True  # Если номенклатура не выбрана, пропускаем все
    
    # Если выбрана позиция "Все лоты", пропускаем все лоты без фильтрации
    if ALL_LOTS_KEY in nomenclature_list:
        return True
    
    lot_name_lower = lot_name.lower()
    
    for nomenclature in nomenclature_list:
        keywords = get_nomenclature_keywords(nomenclature)
        # Если список ключевых слов пустой (например, для "Все лоты"), пропускаем
        if not keywords:
            continue
        if any(keyword in lot_name_lower for keyword in keywords):
            return True
    
    return False


async def check_nomenclature_match_with_llm(
    lot_title: str,
    lot_nomenclature: Optional[List[str] | Dict] = None,
    lot_description: Optional[str] = None,
    nomenclature_list: List[str] = None
) -> bool:
    """
    Проверяет соответствие номенклатуры лота выбранным номенклатурным группам
    с использованием LLM для семантического сопоставления.
    
    Сначала пытается использовать простое сопоставление по ключевым словам.
    Если простое сопоставление не дает результата, использует LLM для семантического анализа.
    
    Args:
        lot_title: Название лота
        lot_nomenclature: Номенклатура из лота (список строк или словарь)
        lot_description: Описание лота (опционально, для более точного анализа)
        nomenclature_list: Список выбранных номенклатурных групп из настроек
    
    Returns:
        True если лот соответствует хотя бы одной номенклатурной группе
    """
    if not nomenclature_list:
        return True
    
    # Если выбрана позиция "Все лоты", пропускаем все лоты без фильтрации
    if ALL_LOTS_KEY in nomenclature_list:
        return True
    
    # Сначала пробуем простое сопоставление по ключевым словам
    simple_match = check_nomenclature_match(lot_title, nomenclature_list)
    if simple_match:
        logger.debug(f"Simple nomenclature match found for: {lot_title[:50]}")
        return True
    
    # Если простое сопоставление не дало результата, используем LLM
    try:
        from services.ai.perplexity import ask_perplexity
        
        # Формируем текст для анализа
        lot_text_parts = [lot_title]
        if lot_description:
            lot_text_parts.append(f"Описание: {lot_description[:500]}")  # Ограничиваем длину
        
        # Обрабатываем номенклатуру из лота
        if lot_nomenclature:
            if isinstance(lot_nomenclature, dict):
                # Если это словарь, извлекаем значения
                nom_items = []
                for key, value in lot_nomenclature.items():
                    if isinstance(value, list):
                        nom_items.extend([str(v) for v in value])
                    else:
                        nom_items.append(str(value))
                if nom_items:
                    lot_text_parts.append(f"Номенклатура в лоте: {', '.join(nom_items[:10])}")
            elif isinstance(lot_nomenclature, list):
                nom_str = ', '.join([str(item) for item in lot_nomenclature[:10]])
                if nom_str:
                    lot_text_parts.append(f"Номенклатура в лоте: {nom_str}")
        
        lot_text = "\n".join(lot_text_parts)
        
        # Формируем список номенклатурных групп с их ключевыми словами для контекста
        nomenclature_context = []
        for nom_group in nomenclature_list:
            keywords = get_nomenclature_keywords(nom_group)
            if keywords:
                nomenclature_context.append(f"- {nom_group}: {', '.join(keywords[:5])}")
        
        nomenclature_context_str = "\n".join(nomenclature_context)
        
        # Формируем промпт для LLM
        system_prompt = """Ты эксперт по классификации товаров и номенклатуре в промышленных закупках.
Твоя задача - определить, относится ли товар/услуга из лота к указанным номенклатурным группам.

Отвечай ТОЛЬКО "ДА" или "НЕТ" без дополнительных пояснений."""
        
        user_prompt = f"""Определи, относится ли товар/услуга из следующего лота к одной из указанных номенклатурных групп:

<ДАННЫЕ ЛОТА>
{lot_text}
</ДАННЫЕ ЛОТА>

<НОМЕНКЛАТУРНЫЕ ГРУППЫ ИЗ НАСТРОЕК>
{nomenclature_context_str}
</НОМЕНКЛАТУРНЫЕ ГРУППЫ ИЗ НАСТРОЕК>

<ИНСТРУКЦИЯ>
Проанализируй семантически и логически:
1. Определи, к какой категории относится товар/услуга из лота
2. Проверь, входит ли эта категория в одну из указанных номенклатурных групп
3. Учитывай, что названия могут отличаться, но товар может относиться к той же категории
4. Например: "болты М12" относятся к "Метизы и крепёжные изделия", даже если в названии нет слова "метиз"

Ответь ТОЛЬКО "ДА" если товар относится хотя бы к одной группе, или "НЕТ" если не относится ни к одной.
</ИНСТРУКЦИЯ>"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Вызываем LLM с коротким ответом
        response = await ask_perplexity(messages, temperature=0.1, max_tokens=50)
        
        # Парсим ответ
        response_upper = response.strip().upper()
        if "ДА" in response_upper or "YES" in response_upper:
            logger.info(f"LLM confirmed nomenclature match for: {lot_title[:50]}")
            return True
        else:
            logger.debug(f"LLM rejected nomenclature match for: {lot_title[:50]}")
            return False
            
    except Exception as e:
        logger.error(f"Error in LLM nomenclature matching: {e}", exc_info=True)
        # В случае ошибки возвращаем False (не пропускаем лот, если не уверены)
        return False


async def check_nomenclature_match_enhanced(
    lot_title: str,
    lot_nomenclature: Optional[List[str] | Dict] = None,
    lot_description: Optional[str] = None,
    nomenclature_list: List[str] = None,
    use_llm: bool = True
) -> bool:
    """
    Улучшенная проверка соответствия номенклатуры с возможностью использования LLM.
    
    Сначала пытается использовать простое сопоставление по ключевым словам.
    Если простое сопоставление не дает результата и use_llm=True, использует LLM.
    
    Args:
        lot_title: Название лота
        lot_nomenclature: Номенклатура из лота (список строк или словарь)
        lot_description: Описание лота (опционально)
        nomenclature_list: Список выбранных номенклатурных групп из настроек
        use_llm: Использовать ли LLM для семантического сопоставления при отсутствии точного совпадения
    
    Returns:
        True если лот соответствует хотя бы одной номенклатурной группе
    """
    if not nomenclature_list:
        return True
    
    if ALL_LOTS_KEY in nomenclature_list:
        return True
    
    # Сначала пробуем простое сопоставление
    simple_match = check_nomenclature_match(lot_title, nomenclature_list)
    if simple_match:
        return True
    
    # Если простое сопоставление не дало результата и разрешено использование LLM
    if use_llm:
        return await check_nomenclature_match_with_llm(
            lot_title,
            lot_nomenclature,
            lot_description,
            nomenclature_list
        )
    
    return False



