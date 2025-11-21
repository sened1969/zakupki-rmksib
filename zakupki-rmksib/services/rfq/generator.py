"""Генератор запросов коммерческого предложения (RFQ)"""
import re
from typing import Optional
from loguru import logger
from services.rfq.web_parser import (
    extract_website_urls_from_text,
    extract_emails_from_multiple_websites
)


def extract_emails_from_text(text: str) -> list[str]:
    """Извлекает email адреса из текста"""
    # Паттерн для поиска email адресов
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text, re.IGNORECASE)
    # Убираем дубликаты и возвращаем уникальные email
    return list(set(emails))


async def parse_supplier_info_from_report(report_text: str, parse_websites: bool = True, max_companies: int = 20) -> dict:
    """
    Парсит информацию о поставщиках из отчета поиска.
    
    Args:
        report_text: Текст отчета поиска поставщиков
        parse_websites: Если True, парсит веб-сайты для поиска email адресов
        max_companies: Максимальное количество компаний с email для возврата (по умолчанию 20)
    
    Returns:
        Словарь с информацией о поставщиках (emails, companies)
        companies ограничены max_companies и содержат только компании с email
    """
    # Извлекаем email адреса напрямую из текста
    emails = extract_emails_from_text(report_text)
    
    # Попытка извлечь названия компаний и контакты
    companies = []
    lines = report_text.split('\n')
    
    current_company = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Попытка найти название компании (обычно в начале строки или после цифры/маркера)
        if re.match(r'^[\d\-\•\*]\s*[А-ЯЁA-Z]', line) or re.match(r'^[А-ЯЁA-Z][а-яёa-z]+\s', line):
            if current_company:
                # Добавляем компанию только если у неё есть email
                if current_company.get('email'):
                    companies.append(current_company)
            current_company = {
                'name': line.lstrip('1234567890.-•* '),
                'email': None,
                'phone': None,
                'website': None
            }
        elif current_company:
            # Поиск email
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
            if email_match:
                current_company['email'] = email_match.group()
            
            # Поиск телефона
            phone_match = re.search(r'[\+]?[0-9\s\-\(\)]{10,}', line)
            if phone_match:
                current_company['phone'] = phone_match.group().strip()
            
            # Поиск сайта
            website_match = re.search(r'https?://[^\s]+|www\.[^\s]+', line)
            if website_match:
                current_company['website'] = website_match.group()
    
    if current_company and current_company.get('email'):
        companies.append(current_company)
    
    # Ограничиваем количество компаний до max_companies
    companies = companies[:max_companies]
    
    # Обновляем список emails только из компаний с email (ограниченных max_companies)
    emails_from_companies = [c['email'] for c in companies if c.get('email')]
    # Объединяем с общими emails, но ограничиваем общее количество
    all_emails = list(set(emails_from_companies + emails))[:max_companies * 2]  # Небольшой запас для парсинга сайтов
    
    # Если нужно парсить веб-сайты для поиска дополнительных email
    if parse_websites:
        # Извлекаем URL веб-сайтов из текста
        website_urls = extract_website_urls_from_text(report_text)
        
        if website_urls:
            logger.info(f"Found {len(website_urls)} websites to parse for emails")
            try:
                # Парсим веб-сайты для поиска email адресов
                website_emails = await extract_emails_from_multiple_websites(website_urls)
                
                # Объединяем найденные email, но ограничиваем общее количество
                emails_set = set(all_emails)
                emails_set.update(website_emails)
                emails = list(emails_set)
                
                logger.info(f"Found {len(website_emails)} additional emails from websites, total: {len(emails)}")
                
                # Обновляем email для компаний, у которых найден сайт
                for company in companies:
                    if company.get('website') and not company.get('email'):
                        # Ищем email для этой компании по домену
                        domain = company['website'].replace('https://', '').replace('http://', '').split('/')[0]
                        company_emails = [e for e in website_emails if domain.lower() in e.lower()]
                        if company_emails:
                            company['email'] = company_emails[0]
            
            except Exception as e:
                logger.warning(f"Error parsing websites for emails: {e}")
    
    # Финальная фильтрация: оставляем только компании с email и ограничиваем до max_companies
    companies_with_email = [c for c in companies if c.get('email')]
    companies = companies_with_email[:max_companies]
    
    # Обновляем emails только из финального списка компаний
    final_emails = [c['email'] for c in companies if c.get('email')]
    # Добавляем дополнительные emails из общего списка, но ограничиваем
    final_emails_set = set(final_emails)
    for email in emails:
        if len(final_emails_set) >= max_companies:
            break
        final_emails_set.add(email)
    emails = list(final_emails_set)[:max_companies]
    
    logger.info(f"Final result: {len(companies)} companies with email, {len(emails)} total emails (limited to {max_companies})")
    
    return {
        'emails': emails,
        'companies': companies
    }


def generate_rfq_text(
    product_name: str = None,
    products: Optional[list] = None,
    product_details: Optional[dict] = None,
    manager_name: Optional[str] = None,
    manager_position: Optional[str] = None,
    manager_phone: Optional[str] = None,
    manager_email: Optional[str] = None,
    company_inn: Optional[str] = None
) -> str:
    """
    Генерирует текст запроса коммерческого предложения
    
    Args:
        product_name: Название товара (для обратной совместимости, если products не указан)
        products: Список товаров [{"name": "...", "quantity": "...", "code": "..."}, ...]
        product_details: Детали товара (резьба, длина, параметры, ГОСТ и т.д.)
        manager_name: Имя и фамилия менеджера
        manager_position: Должность менеджера
        manager_phone: Телефон менеджера
        manager_email: Email менеджера
        company_inn: ИНН компании
    """
    
    # Если передан список товаров, используем его, иначе используем product_name для обратной совместимости
    if products is None:
        if product_name:
            products = [{"name": product_name, "quantity": None, "code": None}]
        else:
            raise ValueError("Необходимо указать либо product_name, либо products")
    
    # Парсинг деталей товара из названия, если они не указаны
    if product_details is None:
        product_details = {}
    
    # Формирование текста запроса
    rfq_text = "Уважаемые коллеги!\n\n"
    rfq_text += "ООО «РМКСИБ» рассматривает возможность закупки крепежных изделий и просит предоставить коммерческое предложение на поставку следующей продукции:\n\n"
    
    # Добавляем список всех товаров с количеством и единицами измерения
    rfq_text += "Перечень номенклатуры:\n\n"
    for idx, product in enumerate(products, 1):
        product_name_item = product.get("name", "")
        quantity = product.get("quantity")
        unit = product.get("unit")
        code = product.get("code")
        
        rfq_text += f"{idx}. Наименование товара: {product_name_item}\n"
        if quantity and unit:
            rfq_text += f"   Требуемое количество: {quantity} {unit}\n"
        elif quantity:
            rfq_text += f"   Требуемое количество: {quantity}\n"
        elif unit:
            rfq_text += f"   Единица измерения: {unit}\n"
            rfq_text += f"   Требуемое количество: уточняется\n"
        else:
            rfq_text += f"   Требуемое количество: уточняется\n"
        if code:
            rfq_text += f"   Код номенклатуры: {code}\n"
        rfq_text += "\n"
    
    rfq_text += "Технические требования:\n\n"
    
    # Для первого товара извлекаем детали (если нужно)
    if products and len(products) > 0:
        first_product_name = products[0].get("name", "")
        
        # Извлечение параметров из названия товара (например: Шпилька ВМ27-6gх140.55.35.I.098 ГОСТ 9066-75)
        # Резьба
        thread_match = re.search(r'[ММ](\d+)[-]?([\w]+)?', first_product_name)
        if thread_match and 'thread' not in product_details:
            product_details['thread'] = f"М{thread_match.group(1)}-{thread_match.group(2) if thread_match.group(2) else '6g'}"
        
        # Длина
        length_match = re.search(r'(\d+)\s*мм|х(\d+)', first_product_name)
        if length_match and 'length' not in product_details:
            length = length_match.group(1) or length_match.group(2)
            product_details['length'] = f"{length} мм"
        
        # Параметры (числа через точку, например 55.35)
        params_match = re.search(r'(\d+\.\d+)', first_product_name)
        if params_match and 'parameters' not in product_details:
            product_details['parameters'] = params_match.group(1)
        
        # Исполнение (I.098 или подобное)
        exec_match = re.search(r'([IVX]+\.\d+)', first_product_name)
        if exec_match and 'execution' not in product_details:
            product_details['execution'] = exec_match.group(1)
        
        # ГОСТ
        gost_match = re.search(r'ГОСТ\s*(\d+[-]\d+)', first_product_name)
        if gost_match and 'gost' not in product_details:
            product_details['gost'] = gost_match.group(1)
    
    # Материал по умолчанию
    if 'material' not in product_details:
        product_details['material'] = 'Сталь 09Г2С (предпочтительно)'
    
    if product_details.get('thread'):
        rfq_text += f"Резьба: {product_details['thread']}\n"
    if product_details.get('length'):
        rfq_text += f"Длина: {product_details['length']}\n"
    if product_details.get('parameters'):
        rfq_text += f"Параметры: {product_details['parameters']}\n"
    if product_details.get('execution'):
        rfq_text += f"Исполнение: {product_details['execution']}\n"
    if product_details.get('gost'):
        rfq_text += f"ГОСТ: {product_details['gost']}\n"
    if product_details.get('material'):
        rfq_text += f"Материал: {product_details['material']}\n"
    
    rfq_text += "\nТребуемая информация:\n\n"
    rfq_text += "• Цена за единицу (с НДС и без НДС)\n"
    rfq_text += "• Срок изготовления/поставки\n"
    rfq_text += "• Условия оплаты\n"
    rfq_text += "• Стоимость и условия доставки\n"
    rfq_text += "• Наличие сертификатов соответствия и паспортов качества\n"
    rfq_text += "• Возможность производства под заказ при отсутствии на складе\n"
    rfq_text += "• Гарантийные обязательства\n\n"
    
    rfq_text += "Дополнительно просим указать:\n\n"
    rfq_text += "• Наличие аналогов при отсутствии точной маркировки\n"
    rfq_text += "• Возможность долгосрочного сотрудничества\n"
    rfq_text += "• Скидки при увеличении объема закупки\n\n"
    
    rfq_text += "Просим предоставить коммерческое предложение в течение 3 рабочих дней с момента получения данного запроса.\n\n"
    rfq_text += "Данный запрос не является офертой и не влечет за собой возникновения каких-либо обязательств со стороны ООО «РМКСИБ».\n\n"
    
    rfq_text += "С уважением,\n"
    if manager_name:
        rfq_text += f"{manager_name}\n"
    if manager_position:
        rfq_text += f"{manager_position}\n"
    rfq_text += "ООО «РМКСИБ»\n\n"
    
    rfq_text += "Контактные данные:\n"
    if manager_phone:
        rfq_text += f"Тел.: {manager_phone}\n"
    if manager_email:
        rfq_text += f"Email: {manager_email}\n"
    if company_inn:
        rfq_text += f"ИНН: {company_inn}\n"
    
    return rfq_text


def generate_rfq_text_from_document(
    products: list,
    manager_name: Optional[str] = None,
    manager_position: Optional[str] = None,
    manager_phone: Optional[str] = None,
    manager_email: Optional[str] = None,
    company_inn: Optional[str] = None
) -> str:
    """
    Генерирует текст запроса коммерческого предложения для случая поиска через документ.
    В этой форме НЕ включаются:
    - Код номенклатуры
    - Технические требования (включая описание технических требований)
    
    Args:
        products: Список товаров [{"name": "...", "quantity": "..."}, ...]
        manager_name: Имя и фамилия менеджера
        manager_position: Должность менеджера
        manager_phone: Телефон менеджера
        manager_email: Email менеджера
        company_inn: ИНН компании
    """
    
    if not products:
        raise ValueError("Необходимо указать список товаров")
    
    # Формирование текста запроса
    rfq_text = "Уважаемые коллеги!\n\n"
    rfq_text += "ООО «РМКСИБ» рассматривает возможность закупки крепежных изделий и просит предоставить коммерческое предложение на поставку следующей продукции:\n\n"
    
    # Добавляем список всех товаров с количеством и единицами измерения (БЕЗ кода номенклатуры)
    rfq_text += "Перечень номенклатуры:\n\n"
    for idx, product in enumerate(products, 1):
        product_name_item = product.get("name", "")
        quantity = product.get("quantity")
        unit = product.get("unit")
        
        rfq_text += f"{idx}. Наименование товара: {product_name_item}\n"
        if quantity and unit:
            rfq_text += f"   Требуемое количество: {quantity} {unit}\n"
        elif quantity:
            rfq_text += f"   Требуемое количество: {quantity}\n"
        elif unit:
            rfq_text += f"   Единица измерения: {unit}\n"
            rfq_text += f"   Требуемое количество: уточняется\n"
        else:
            rfq_text += f"   Требуемое количество: уточняется\n"
        rfq_text += "\n"
    
    # Пропускаем раздел "Технические требования" полностью
    
    rfq_text += "Требуемая информация:\n\n"
    rfq_text += "• Цена за единицу (с НДС и без НДС)\n"
    rfq_text += "• Срок изготовления/поставки\n"
    rfq_text += "• Условия оплаты\n"
    rfq_text += "• Стоимость и условия доставки\n"
    rfq_text += "• Наличие сертификатов соответствия и паспортов качества\n"
    rfq_text += "• Возможность производства под заказ при отсутствии на складе\n"
    rfq_text += "• Гарантийные обязательства\n\n"
    
    rfq_text += "Дополнительно просим указать:\n\n"
    rfq_text += "• Наличие аналогов при отсутствии точной маркировки\n"
    rfq_text += "• Возможность долгосрочного сотрудничества\n"
    rfq_text += "• Скидки при увеличении объема закупки\n\n"
    
    rfq_text += "Просим предоставить коммерческое предложение в течение 3 рабочих дней с момента получения данного запроса.\n\n"
    rfq_text += "Данный запрос не является офертой и не влечет за собой возникновения каких-либо обязательств со стороны ООО «РМКСИБ».\n\n"
    
    rfq_text += "С уважением,\n"
    if manager_name:
        rfq_text += f"{manager_name}\n"
    if manager_position:
        rfq_text += f"{manager_position}\n"
    rfq_text += "ООО «РМКСИБ»\n\n"
    
    rfq_text += "Контактные данные:\n"
    if manager_phone:
        rfq_text += f"Тел.: {manager_phone}\n"
    if manager_email:
        rfq_text += f"Email: {manager_email}\n"
    if company_inn:
        rfq_text += f"ИНН: {company_inn}\n"
    
    return rfq_text

