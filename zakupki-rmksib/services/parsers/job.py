from __future__ import annotations
from loguru import logger
from typing import List, Dict
from services.parsers import fetch_new_lots
from database import async_session_maker, LotRepository, UserRepository, UserPreferenceRepository
from services.notifications import send_email
from utils.formatters import format_rub, format_date
from config.settings import settings


def _matches_preferences(
	lot: Dict,
	customers: List[str] | None,
	nomenclature: List[str] | None,
	budget_min: int | None = None,
	budget_max: int | None = None
) -> bool:
	"""Проверяет соответствие лота настройкам пользователя"""
	cust_ok = True
	nom_ok = True
	budget_ok = True
	
	if customers:
		cust_ok = (lot.get("customer") in customers)
	
	if nomenclature:
		# Используем функцию проверки номенклатуры из config
		from config.nomenclature import check_nomenclature_match
		nom_ok = check_nomenclature_match(lot.get("title", ""), nomenclature)
	
	# Проверка бюджета
	if budget_min is not None or budget_max is not None:
		budget = lot.get("budget", 0)
		if budget_min is not None and budget < budget_min:
			budget_ok = False
		if budget_max is not None and budget > budget_max:
			budget_ok = False
	
	return cust_ok and nom_ok and budget_ok


async def run_parsers_once() -> int:
	"""Fetch new lots and upsert them into the database, then notify interested users."""
	new_count = 0
	created: List[Dict] = []
	lots: List[Dict] = await fetch_new_lots()
	if not lots:
		logger.info("Parser returned no lots")
		return 0

	async with async_session_maker() as session:
		repo = LotRepository(session)
		for data in lots:
			lot_number = data.get("lot_number")
			if not lot_number:
				continue
			exists = await repo.get_by_lot_number(lot_number)
			if exists:
				continue
			
			# Фильтруем данные, оставляя только поля модели Lot
			# Удаляем поля, которых нет в модели: url, publish_date, parsed_at
			lot_data = {
				"platform_name": data.get("platform_name"),
				"lot_number": data.get("lot_number"),
				"title": data.get("title"),
				"description": data.get("description"),
				"budget": data.get("budget", 0.0),
				"deadline": data.get("deadline"),
				"status": data.get("status", "active"),
				"review_status": "not_viewed",  # По умолчанию не просмотрен
			}
			# Добавляем опциональные поля только если они не None
			if data.get("customer"):
				lot_data["customer"] = data.get("customer")
			if data.get("nomenclature"):
				lot_data["nomenclature"] = data.get("nomenclature")
			if data.get("url"):
				lot_data["url"] = data.get("url")
			if data.get("source"):
				lot_data["source"] = data.get("source")
			else:
				lot_data["source"] = "parser"  # Значение по умолчанию
			
			# Создаем лот в БД
			lot = await repo.create(**lot_data)
			created.append(data)
			new_count += 1
			
			# Автоматически скачиваем документацию, если есть URL
			if data.get("url") and lot:
				try:
					from services.documentation import download_documentation_from_url, extract_text_from_file
					logger.info(f"Auto-downloading documentation for lot {lot.lot_number} from {data.get('url')}")
					
					# Скачиваем документацию
					file_path = await download_documentation_from_url(data.get("url"), lot.lot_number)
					
					if file_path:
						# Извлекаем текст
						documentation_text = await extract_text_from_file(file_path)
						
						# Обновляем лот в БД
						lot.documentation_path = file_path
						lot.documentation_text = documentation_text if documentation_text and not documentation_text.startswith("[Ошибка") else None
						lot.documentation_analyzed = False
						await repo.update(lot)
						
						logger.info(f"Documentation auto-downloaded for lot {lot.lot_number}: {file_path}")
					else:
						logger.warning(f"Could not auto-download documentation for lot {lot.lot_number}")
				except Exception as e:
					logger.error(f"Error auto-downloading documentation for lot {lot.lot_number}: {e}", exc_info=True)
					# Не прерываем процесс парсинга из-за ошибки скачивания документации

	logger.info(f"Parser job: created {new_count} new lots")

	if new_count > 0:
		# Build personalized recipients map: email -> list of lots
		user_repo = UserRepository
		pref_repo = UserPreferenceRepository
		personal: dict[str, List[Dict]] = {}
		async with async_session_maker() as session:
			u_repo = user_repo(session)
			p_repo = pref_repo(session)
			active_users = await u_repo.get_all_active(limit=10000)
			for user in active_users:
				if user.role not in {"admin", "manager"}:
					continue
				if not user.contact_email:
					continue
				pref = await p_repo.get_or_create(user.id)
				if not pref.notify_enabled:
					continue
				# Фильтруем с учетом бюджета
				user_lots = [
					d for d in created
					if _matches_preferences(
						d,
						pref.customers,
						pref.nomenclature,
						pref.budget_min,
						pref.budget_max
					)
				]
				if user_lots:
					personal[user.contact_email] = user_lots
		# Fallback to global list if no matches for anyone
		if not personal and settings.NOTIFY_EMAILS:
			personal = {email: created for email in settings.NOTIFY_EMAILS}

		# Send per-user digests
		for email, lots_list in personal.items():
			subject = f"Новые закупки ({len(lots_list)})"
			rows = []
			for d in lots_list:
				rows.append(
					f"<li><b>{d['title']}</b> — {format_rub(float(d['budget']))}, дедлайн {format_date(d['deadline'])}, заказчик {d.get('customer') or '-'}, № {d['lot_number']}</li>"
				)
			body = (
				"<p>Подходящие новые лоты:</p>"
				f"<ul>{''.join(rows)}</ul>"
				"<p>Это автописьмо бота Закупки РМКСИБ.</p>"
			)
			await send_email(subject, body, [email])

	return new_count


async def run_parser_for_customer(customer_name: str) -> tuple[int, str]:
	"""
	Запускает парсер для конкретного заказчика
	
	Args:
		customer_name: Название заказчика
	
	Returns:
		Кортеж (количество новых лотов, сообщение о результате)
	"""
	from config.customers import get_customer_info, CUSTOMERS_CATALOG
	
	customer_info = get_customer_info(customer_name)
	
	if not customer_info:
		return 0, f"❌ Заказчик '{customer_name}' не найден в справочнике."
	
	parser_type = customer_info.get("parser_type")
	is_active = customer_info.get("is_active", False)
	
	if not parser_type or not is_active:
		return 0, "Требуется настроить Прямой запрос к B2B-Center API"
	
	# Запускаем соответствующий парсер
	if parser_type == "pavlik_static":
		from services.parsers.pavlik_parser import PavlikParser
		parser = PavlikParser()
		try:
			lots = await parser.parse_current_lots()
		except Exception as e:
			logger.error(f"Error parsing {customer_name}: {e}", exc_info=True)
			return 0, f"❌ Ошибка при парсинге: {str(e)}"
	else:
		return 0, f"❌ Парсер типа '{parser_type}' не реализован."
	
	if not lots:
		return 0, "📭 Новых лотов не найдено."
	
	# Сохраняем лоты в БД
	new_count = 0
	created: List[Dict] = []
	
	async with async_session_maker() as session:
		repo = LotRepository(session)
		for data in lots:
			# Убеждаемся, что заказчик установлен
			if not data.get("customer"):
				data["customer"] = customer_name
			
			lot_number = data.get("lot_number")
			if not lot_number:
				continue
			
			exists = await repo.get_by_lot_number(lot_number)
			if exists:
				continue
			
			# Фильтруем данные, оставляя только поля модели Lot
			# Удаляем поля, которых нет в модели: url, publish_date, parsed_at
			lot_data = {
				"platform_name": data.get("platform_name"),
				"lot_number": data.get("lot_number"),
				"title": data.get("title"),
				"description": data.get("description"),
				"budget": data.get("budget", 0.0),
				"deadline": data.get("deadline"),
				"status": data.get("status", "active"),
				"review_status": "not_viewed",  # По умолчанию не просмотрен
			}
			# Добавляем опциональные поля только если они не None
			if data.get("customer"):
				lot_data["customer"] = data.get("customer")
			if data.get("nomenclature"):
				lot_data["nomenclature"] = data.get("nomenclature")
			if data.get("url"):
				lot_data["url"] = data.get("url")
			if data.get("source"):
				lot_data["source"] = data.get("source")
			else:
				lot_data["source"] = "parser"  # Значение по умолчанию
			
			# Создаем лот в БД
			lot = await repo.create(**lot_data)
			created.append(data)
			new_count += 1
			
			# Автоматически скачиваем документацию, если есть URL
			if data.get("url") and lot:
				try:
					from services.documentation import download_documentation_from_url, extract_text_from_file
					logger.info(f"Auto-downloading documentation for lot {lot.lot_number} from {data.get('url')}")
					
					# Скачиваем документацию
					file_path = await download_documentation_from_url(data.get("url"), lot.lot_number)
					
					if file_path:
						# Извлекаем текст
						documentation_text = await extract_text_from_file(file_path)
						
						# Обновляем лот в БД
						lot.documentation_path = file_path
						lot.documentation_text = documentation_text if documentation_text and not documentation_text.startswith("[Ошибка") else None
						lot.documentation_analyzed = False
						await repo.update(lot)
						
						logger.info(f"Documentation auto-downloaded for lot {lot.lot_number}: {file_path}")
					else:
						logger.warning(f"Could not auto-download documentation for lot {lot.lot_number}")
				except Exception as e:
					logger.error(f"Error auto-downloading documentation for lot {lot.lot_number}: {e}", exc_info=True)
					# Не прерываем процесс парсинга из-за ошибки скачивания документации
	
	if new_count == 0:
		return 0, "📭 Новых лотов не найдено (все уже есть в базе)."
	
	logger.info(f"Parser for {customer_name}: created {new_count} new lots")
	
	# Формируем сообщение о результате
	message = f"✅ <b>Запрос выполнен успешно!</b>\n\n"
	message += f"📊 Найдено новых лотов: {new_count}\n\n"
	
	# Показываем первые 5 лотов
	for idx, lot in enumerate(created[:5], 1):
		message += f"{idx}. {lot.get('title', 'Без названия')[:50]}...\n"
		message += f"   💰 {format_rub(float(lot.get('budget', 0)))}\n"
		message += f"   🆔 {lot.get('lot_number', 'N/A')}\n\n"
	
	if len(created) > 5:
		message += f"... и еще {len(created) - 5} лотов"
	
	return new_count, message


async def cleanup_expired_lots(days_before_expiry: int = 0) -> int:
	"""
	Очистка лотов с прошедшим дедлайном
	
	Args:
		days_before_expiry: Количество дней до истечения дедлайна (по умолчанию 0 - только уже прошедшие)
	                      Если > 0, то удаляются лоты, у которых дедлайн истекает в течение этого количества дней
	
	Returns:
		Количество удаленных лотов
	"""
	from database import async_session_maker, LotRepository
	
	try:
		async with async_session_maker() as session:
			repo = LotRepository(session)
			deleted_count = await repo.delete_expired_lots(days_before_expiry)
		
		if deleted_count > 0:
			if days_before_expiry == 0:
				logger.info(f"Cleanup: deleted {deleted_count} expired lots (deadline < now)")
			else:
				logger.info(f"Cleanup: deleted {deleted_count} expired lots (deadline < now - {days_before_expiry} day(s))")
		else:
			logger.info("Cleanup: no expired lots to delete")
		
		return deleted_count
	except Exception as e:
		logger.error(f"Error during cleanup of expired lots: {e}", exc_info=True)
		return 0
