"""Парсер веб-страниц для извлечения email адресов со страниц контактов поставщиков"""
import re
import asyncio
from typing import Optional, List, Set
from urllib.parse import urljoin, urlparse
from loguru import logger
import httpx
from bs4 import BeautifulSoup

# Таймауты для HTTP запросов
HTTP_TIMEOUT = 10  # секунд
MAX_CONCURRENT_REQUESTS = 5  # максимум параллельных запросов

# Паттерны для поиска страниц контактов
CONTACT_PAGE_PATTERNS = [
    r'/contact',
    r'/contacts',
    r'/kontakty',
    r'/kontakt',
    r'/about',
    r'/about-us',
    r'/o-nas',
    r'/company',
    r'/company-info',
    r'/info',
]

# Паттерн для поиска email адресов
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE)

# Исключаемые email адреса (служебные)
EXCLUDED_EMAIL_PATTERNS = [
    r'example\.com',
    r'test\.com',
    r'sample\.com',
    r'noreply@',
    r'no-reply@',
    r'donotreply@',
    r'webmaster@',
    r'admin@',
    r'info@',  # Можно оставить, но с осторожностью
]


def is_valid_email(email: str) -> bool:
    """Проверяет, является ли email валидным и не служебным"""
    if not email or len(email) < 5:
        return False
    
    # Проверяем на исключаемые паттерны
    for pattern in EXCLUDED_EMAIL_PATTERNS:
        if re.search(pattern, email, re.IGNORECASE):
            return False
    
    # Проверяем базовый формат
    if not EMAIL_PATTERN.match(email):
        return False
    
    return True


def find_contact_page_url(base_url: str, soup: BeautifulSoup) -> Optional[str]:
    """Находит URL страницы контактов на сайте"""
    # Нормализуем базовый URL
    parsed_base = urlparse(base_url)
    base_scheme = parsed_base.scheme or 'https'
    base_netloc = parsed_base.netloc
    
    if not base_netloc:
        return None
    
    full_base = f"{base_scheme}://{base_netloc}"
    
    # Ищем ссылки на страницы контактов
    links = soup.find_all('a', href=True)
    contact_urls = []
    
    for link in links:
        href = link.get('href', '')
        text = link.get_text().lower().strip()
        
        # Проверяем текст ссылки
        if any(word in text for word in ['контакт', 'контакты', 'contact', 'contacts', 'связаться', 'связь']):
            full_url = urljoin(full_base, href)
            contact_urls.append(full_url)
        
        # Проверяем URL на паттерны страниц контактов
        href_lower = href.lower()
        for pattern in CONTACT_PAGE_PATTERNS:
            if re.search(pattern, href_lower):
                full_url = urljoin(full_base, href)
                contact_urls.append(full_url)
                break
    
    # Возвращаем первый найденный URL
    if contact_urls:
        return contact_urls[0]
    
    # Если не нашли, пробуем стандартные пути
    for pattern in CONTACT_PAGE_PATTERNS:
        test_url = urljoin(full_base, pattern)
        contact_urls.append(test_url)
    
    return contact_urls[0] if contact_urls else None


def extract_emails_from_html(html: str, base_url: Optional[str] = None) -> Set[str]:
    """Извлекает email адреса из HTML кода"""
    emails = set()
    
    # Поиск в тексте
    text_emails = EMAIL_PATTERN.findall(html)
    for email in text_emails:
        email = email.lower().strip()
        if is_valid_email(email):
            emails.add(email)
    
    # Поиск в атрибутах (href="mailto:...")
    mailto_pattern = re.compile(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE)
    mailto_emails = mailto_pattern.findall(html)
    for email in mailto_emails:
        email = email.lower().strip()
        if is_valid_email(email):
            emails.add(email)
    
    # Парсинг через BeautifulSoup
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Поиск в тексте всех элементов
        all_text = soup.get_text()
        text_emails = EMAIL_PATTERN.findall(all_text)
        for email in text_emails:
            email = email.lower().strip()
            if is_valid_email(email):
                emails.add(email)
        
        # Поиск в ссылках mailto
        mailto_links = soup.find_all('a', href=re.compile(r'mailto:', re.I))
        for link in mailto_links:
            href = link.get('href', '')
            match = mailto_pattern.search(href)
            if match:
                email = match.group(1).lower().strip()
                if is_valid_email(email):
                    emails.add(email)
        
        # Поиск в специальных элементах с email (может быть в data-атрибутах)
        email_elements = soup.find_all(string=EMAIL_PATTERN)
        for element in email_elements:
            element_emails = EMAIL_PATTERN.findall(str(element))
            for email in element_emails:
                email = email.lower().strip()
                if is_valid_email(email):
                    emails.add(email)
    
    except Exception as e:
        logger.warning(f"Error parsing HTML with BeautifulSoup: {e}")
    
    return emails


async def fetch_url(url: str, timeout: int = HTTP_TIMEOUT) -> Optional[str]:
    """Загружает HTML содержимое страницы"""
    try:
        # Нормализуем URL
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            # Проверяем, что это HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'html' not in content_type:
                logger.debug(f"URL {url} returned non-HTML content: {content_type}")
                return None
            
            return response.text
    
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error {e.response.status_code} for {url}")
        return None
    except httpx.TimeoutException:
        logger.warning(f"Timeout while fetching {url}")
        return None
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None


async def extract_emails_from_website(base_url: str) -> Set[str]:
    """
    Извлекает email адреса с веб-сайта поставщика.
    
    Args:
        base_url: Базовый URL сайта (может быть с или без протокола)
    
    Returns:
        Множество найденных email адресов
    """
    emails = set()
    
    # Нормализуем URL
    parsed = urlparse(base_url)
    if not parsed.scheme:
        base_url = f"https://{base_url}"
    
    # Загружаем главную страницу
    logger.info(f"Fetching main page: {base_url}")
    main_html = await fetch_url(base_url)
    
    if not main_html:
        logger.warning(f"Could not fetch main page: {base_url}")
        return emails
    
    # Извлекаем email с главной страницы
    main_emails = extract_emails_from_html(main_html, base_url)
    emails.update(main_emails)
    logger.debug(f"Found {len(main_emails)} emails on main page")
    
    # Ищем страницу контактов
    try:
        soup = BeautifulSoup(main_html, 'html.parser')
        contact_url = find_contact_page_url(base_url, soup)
        
        if contact_url and contact_url != base_url:
            logger.info(f"Found contact page: {contact_url}")
            contact_html = await fetch_url(contact_url)
            
            if contact_html:
                contact_emails = extract_emails_from_html(contact_html, contact_url)
                emails.update(contact_emails)
                logger.debug(f"Found {len(contact_emails)} emails on contact page")
    except Exception as e:
        logger.warning(f"Error searching for contact page: {e}")
    
    return emails


async def extract_emails_from_multiple_websites(urls: List[str]) -> Set[str]:
    """
    Извлекает email адреса с нескольких веб-сайтов параллельно.
    
    Args:
        urls: Список URL сайтов
    
    Returns:
        Множество найденных email адресов
    """
    all_emails = set()
    
    # Обрабатываем URL батчами для ограничения параллелизма
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def fetch_with_semaphore(url: str):
        async with semaphore:
            return await extract_emails_from_website(url)
    
    # Запускаем параллельные запросы
    tasks = [fetch_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Собираем результаты
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Error in parallel fetch: {result}")
        elif isinstance(result, set):
            all_emails.update(result)
    
    return all_emails


def extract_website_urls_from_text(text: str) -> List[str]:
    """Извлекает URL веб-сайтов из текста"""
    # Паттерн для поиска URL
    url_pattern = re.compile(
        r'(?:https?://|www\.)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}(?:/[^\s]*)?',
        re.IGNORECASE
    )
    
    urls = url_pattern.findall(text)
    # Нормализуем и очищаем URL
    normalized_urls = []
    seen = set()
    
    for url in urls:
        # Убираем www. если есть https://
        if url.startswith('www.'):
            url = f"https://{url}"
        elif not url.startswith('http'):
            url = f"https://{url}"
        
        # Парсим и нормализуем
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain and domain not in seen:
            normalized_urls.append(domain)
            seen.add(domain)
    
    return normalized_urls
















