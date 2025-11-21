"""Сервис для парсинга контактной информации с сайтов поставщиков"""
import logging
import re
import warnings
from typing import Optional, Dict
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

# Отключаем предупреждения о небезопасных SSL запросах
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logger = logging.getLogger(__name__)


# Паттерны для поиска страниц контактов
CONTACT_PAGE_PATTERNS = [
	'/contact', '/contacts', '/kontakty', '/контакты',
	'/about/contact', '/info/contact', '/company/contact',
	'/contact-us', '/contactus', '/связаться'
]

# Паттерны для поиска email
EMAIL_PATTERN = re.compile(
	r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
	re.IGNORECASE
)

# Паттерны для поиска телефонов (российские форматы)
PHONE_PATTERNS = [
	re.compile(r'\+?7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'),  # +7 (XXX) XXX-XX-XX
	re.compile(r'\+?7[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'),  # +7 XXX XXX XX XX
	re.compile(r'8[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'),  # 8 (XXX) XXX-XX-XX
	re.compile(r'8[\s\-]?\d{10}'),  # 8XXXXXXXXXX
]


def normalize_phone(phone: str) -> str:
	"""Нормализует номер телефона"""
	# Удаляем все нецифровые символы кроме +
	phone = re.sub(r'[^\d+]', '', phone)
	# Заменяем 8 на +7
	if phone.startswith('8'):
		phone = '+7' + phone[1:]
	# Добавляем +7 если начинается с 7
	if phone.startswith('7') and not phone.startswith('+7'):
		phone = '+' + phone
	return phone


def extract_emails(text: str) -> list[str]:
	"""Извлекает email адреса из текста"""
	if not text:
		return []
	
	emails = EMAIL_PATTERN.findall(text)
	# Фильтруем очевидно неправильные email
	valid_emails = []
	for email in emails:
		email_lower = email.lower()
		# Исключаем примеры и placeholder'ы
		skip_patterns = [
			'example.com', 'test@', 'placeholder', 'xxx', 'sample',
			'noreply', 'no-reply', 'donotreply', 'do-not-reply',
			'example@', 'test.com'
		]
		# НЕ исключаем mail.ru и yandex.ru, так как это реальные почтовые сервисы
		# Проверяем, что это не пример
		if not any(skip in email_lower for skip in skip_patterns):
			# Проверяем, что email содержит имя пользователя (до @)
			parts = email.split('@')
			if len(parts) == 2 and parts[0] and len(parts[0]) > 1:
				valid_emails.append(email)
	
	return list(set(valid_emails))  # Убираем дубликаты


def extract_phones(text: str) -> list[str]:
	"""Извлекает номера телефонов из текста"""
	phones = []
	for pattern in PHONE_PATTERNS:
		matches = pattern.findall(text)
		for match in matches:
			normalized = normalize_phone(match)
			if len(normalized) >= 11:  # Минимальная длина российского номера
				phones.append(normalized)
	return list(set(phones))  # Убираем дубликаты


async def find_contact_page(base_url: str) -> Optional[str]:
	"""
	Находит страницу контактов на сайте
	
	Args:
		base_url: Базовый URL сайта
		
	Returns:
		URL страницы контактов или None
	"""
	try:
		parsed = urlparse(base_url)
		if not parsed.scheme:
			base_url = 'https://' + base_url
		
		async with httpx.AsyncClient(
			timeout=10.0, 
			follow_redirects=True,
			verify=False  # Отключаем проверку SSL для проблемных сайтов
		) as client:
			headers = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
			}
			
			# Пробуем основные страницы контактов
			for pattern in CONTACT_PAGE_PATTERNS:
				contact_url = urljoin(base_url, pattern)
				try:
					response = await client.head(contact_url, headers=headers, timeout=5.0)
					if response.status_code == 200:
						logger.debug(f"Found contact page: {contact_url}")
						return contact_url
				except Exception as e:
					logger.debug(f"Failed to check {contact_url}: {e}")
					continue
			
			# Если не нашли через HEAD, пробуем GET для некоторых страниц
			priority_patterns = ['/contact', '/contacts', '/kontakty', '/контакты']
			for pattern in priority_patterns:
				contact_url = urljoin(base_url, pattern)
				try:
					response = await client.get(contact_url, headers=headers, timeout=5.0)
					if response.status_code == 200:
						logger.debug(f"Found contact page via GET: {contact_url}")
						return contact_url
				except Exception:
					continue
			
			# Если не нашли, пробуем парсить главную страницу и искать ссылки
			try:
				response = await client.get(base_url, headers=headers, timeout=10.0)
				if response.status_code == 200:
					soup = BeautifulSoup(response.text, 'html.parser')
					# Ищем ссылки на страницы контактов
					for link in soup.find_all('a', href=True):
						href = link.get('href', '').lower()
						text = link.get_text(strip=True).lower()
						
						# Проверяем паттерны в href
						if any(pattern in href for pattern in CONTACT_PAGE_PATTERNS):
							contact_url = urljoin(base_url, link['href'])
							logger.debug(f"Found contact link in navigation: {contact_url}")
							return contact_url
						
						# Проверяем текст ссылки
						contact_words = ['контакт', 'связаться', 'contact', 'связь', 'написать']
						if any(word in text for word in contact_words) and len(text) < 50:
							contact_url = urljoin(base_url, link['href'])
							# Проверяем, что это не внешняя ссылка
							parsed_link = urlparse(contact_url)
							parsed_base = urlparse(base_url)
							if parsed_link.netloc == parsed_base.netloc or not parsed_link.netloc:
								logger.debug(f"Found contact link by text: {contact_url}")
								return contact_url
			except Exception as e:
				logger.debug(f"Error parsing main page for contact links: {e}")
				pass
				
	except Exception as e:
		logger.warning(f"Error finding contact page for {base_url}: {e}")
	
	return None


async def parse_contacts_from_url(url: str) -> Dict[str, any]:
	"""
	Парсит контактную информацию со страницы
	
	Args:
		url: URL страницы для парсинга
		
	Returns:
		Словарь с контактами: {'emails': [], 'phones': [], 'address': ''}
	"""
	result = {
		'emails': [],
		'phones': [],
		'address': ''
	}
	
	try:
		# Создаем клиент с отключенной проверкой SSL для проблемных сайтов
		# Это необходимо для сайтов с невалидными сертификатами
		async with httpx.AsyncClient(
			timeout=15.0, 
			follow_redirects=True,
			verify=False  # Отключаем проверку SSL для проблемных сайтов
		) as client:
			headers = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
			}
			
			try:
				response = await client.get(url, headers=headers)
				response.raise_for_status()
			except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
				logger.warning(f"Failed to fetch {url}: {e}")
				return result
			
			# Получаем HTML как строку для поиска в исходном коде
			html_content = response.text
			
			soup = BeautifulSoup(html_content, 'html.parser')
			
			# Удаляем скрипты и стили
			for script in soup(["script", "style"]):
				script.decompose()
			
			# СБОР EMAIL ИЗ РАЗНЫХ ИСТОЧНИКОВ
			emails_set = set()
			
			# 1. Ищем email в mailto: ссылках
			for link in soup.find_all('a', href=True):
				href = link.get('href', '')
				if href.startswith('mailto:'):
					email = href.replace('mailto:', '').split('?')[0].split('&')[0].strip()
					if email and EMAIL_PATTERN.match(email):
						emails_set.add(email)
						logger.debug(f"Found email in mailto link: {email}")
			
			# 2. Ищем email в data-атрибутах (data-email, data-contact-email и т.д.)
			try:
				for elem in soup.find_all(attrs=lambda x: x and isinstance(x, dict) and any(attr.startswith('data-') and 'email' in attr.lower() for attr in x.keys())):
					if hasattr(elem, 'attrs') and isinstance(elem.attrs, dict):
						for attr_name, attr_value in elem.attrs.items():
							if 'email' in attr_name.lower() and isinstance(attr_value, str):
								emails_found = extract_emails(attr_value)
								if emails_found:
									logger.debug(f"Found emails in data-attribute {attr_name}: {emails_found}")
								emails_set.update(emails_found)
			except Exception as e:
				logger.debug(f"Error searching in data-attributes: {e}")
			
			# 3. Ищем email в тексте элементов (особенно в блоках контактов)
			# Сначала ищем в специальных блоках контактов
			contact_keywords = ['контакт', 'contact', 'email', 'почта', 'e-mail', 'mail', 'info', 'связь']
			for keyword in contact_keywords:
				try:
					# Ищем элементы с классом или id, содержащим ключевое слово
					for elem in soup.find_all(['div', 'section', 'p', 'span', 'li', 'td'], 
					                         class_=re.compile(keyword, re.I)):
						text = elem.get_text(separator=' ', strip=True)
						emails_found = extract_emails(text)
						if emails_found:
							logger.debug(f"Found {len(emails_found)} emails in element with class containing '{keyword}'")
						emails_set.update(emails_found)
					
					# Ищем элементы с id, содержащим ключевое слово
					for elem in soup.find_all(['div', 'section', 'p', 'span', 'li', 'td'], 
					                         id=re.compile(keyword, re.I)):
						text = elem.get_text(separator=' ', strip=True)
						emails_found = extract_emails(text)
						if emails_found:
							logger.debug(f"Found {len(emails_found)} emails in element with id containing '{keyword}'")
						emails_set.update(emails_found)
					
					# Ищем элементы, содержащие текст с ключевым словом и email рядом
					# Ограничиваем поиск первыми 50 элементами для производительности
					for elem in soup.find_all(['div', 'section', 'p', 'span', 'li', 'td'], limit=50):
						text = elem.get_text(separator=' ', strip=True)
						if keyword.lower() in text.lower() and '@' in text:
							emails_found = extract_emails(text)
							if emails_found:
								logger.debug(f"Found {len(emails_found)} emails near keyword '{keyword}'")
							emails_set.update(emails_found)
				except Exception as e:
					logger.debug(f"Error searching for emails with keyword '{keyword}': {e}")
					continue
			
			# 4. Ищем email во всем тексте страницы
			text = soup.get_text(separator=' ', strip=True)
			emails_found = extract_emails(text)
			if emails_found:
				logger.debug(f"Found {len(emails_found)} emails in page text")
			emails_set.update(emails_found)
			
			# 5. Ищем email в исходном HTML (на случай, если они закодированы или в комментариях)
			emails_found = extract_emails(html_content)
			if emails_found:
				logger.debug(f"Found {len(emails_found)} emails in HTML source")
			emails_set.update(emails_found)
			
			# Конвертируем в список и фильтруем
			emails = list(emails_set)
			result['emails'] = emails
			
			# Извлекаем телефоны
			phones = extract_phones(text)
			result['phones'] = phones
			
			# Пытаемся найти адрес (ищем блоки с адресом)
			address_keywords = ['адрес', 'address', 'location', 'расположение']
			for keyword in address_keywords:
				# Ищем элементы, содержащие ключевые слова
				for elem in soup.find_all(['div', 'p', 'span'], string=re.compile(keyword, re.I)):
					parent = elem.parent
					if parent:
						address_text = parent.get_text(strip=True)
						if len(address_text) > 20 and len(address_text) < 200:
							result['address'] = address_text
							break
				if result['address']:
					break
			
			logger.info(f"Parsed contacts from {url}: {len(emails)} emails, {len(phones)} phones")
			if emails:
				logger.debug(f"Found emails: {', '.join(emails[:3])}")
			else:
				logger.warning(f"No emails found on {url}, tried multiple extraction methods")
			
	except Exception as e:
		logger.error(f"Error parsing contacts from {url}: {e}", exc_info=True)
	
	return result


async def get_supplier_contacts(supplier_name: str, website_url: Optional[str] = None) -> Dict[str, any]:
	"""
	Получает контактную информацию поставщика
	
	Args:
		supplier_name: Название поставщика
		website_url: URL сайта поставщика (опционально)
		
	Returns:
		Словарь с контактами: {'emails': [], 'phones': [], 'address': '', 'website': ''}
	"""
	result = {
		'emails': [],
		'phones': [],
		'address': '',
		'website': website_url or ''
	}
	
	if not website_url:
		logger.warning(f"No website URL provided for {supplier_name}")
		return result
	
	# Находим страницу контактов
	contact_page = await find_contact_page(website_url)
	if not contact_page:
		logger.warning(f"Contact page not found for {website_url}, will parse main page")
		# Пробуем парсить главную страницу
		contact_page = website_url
	else:
		logger.info(f"Found contact page for {supplier_name}: {contact_page}")
	
	# Парсим контакты со страницы контактов
	contacts = await parse_contacts_from_url(contact_page)
	result.update(contacts)
	
	# Если не нашли email на странице контактов, пробуем главную страницу
	if not result['emails'] and contact_page != website_url:
		logger.info(f"No emails found on contact page, trying main page: {website_url}")
		main_page_contacts = await parse_contacts_from_url(website_url)
		# Объединяем результаты (email с главной страницы добавляем, если их нет)
		if main_page_contacts.get('emails'):
			result['emails'].extend(main_page_contacts['emails'])
			result['emails'] = list(set(result['emails']))  # Убираем дубликаты
		if main_page_contacts.get('phones') and not result['phones']:
			result['phones'] = main_page_contacts['phones']
		if main_page_contacts.get('address') and not result['address']:
			result['address'] = main_page_contacts['address']
	
	logger.info(f"Final result for {supplier_name}: {len(result['emails'])} emails, {len(result['phones'])} phones")
	if result['emails']:
		logger.debug(f"Found emails: {', '.join(result['emails'][:3])}")
	
	return result

