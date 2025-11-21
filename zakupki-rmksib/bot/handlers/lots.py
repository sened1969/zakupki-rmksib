"""Обработчики для работы с лотами"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Document, FSInputFile
from bot.states.forms import DocumentationStates, ManualLotCreationStates
from database.models import User, Lot
from database import async_session_maker, LotRepository, UserRepository, UserPreferenceRepository
from utils.formatters import format_rub, format_date, format_separator, format_number
from datetime import datetime
from services.ai import analyze_lot, analyze_documentation
from services.documentation import save_documentation_file, extract_text_from_file, is_supported_format, download_documentation_from_url
from services.notifications import send_email
from config import settings
from bot.keyboards.inline import get_customer_fetch_menu
from pathlib import Path
import logging

router = Router()
logger = logging.getLogger(__name__)


def _analysis_keyboard(lot_number: str, has_documentation: bool = False) -> InlineKeyboardMarkup:
	"""Клавиатура для действий с лотом"""
	keyboard = []
	# Кнопка анализа документации убрана - используется универсальная кнопка "Анализ лота"
	# Параметр has_documentation оставлен для обратной совместимости
	keyboard.append([InlineKeyboardButton(text="📧 Отправить анализ на email", callback_data=f"mail:{lot_number}")])
	return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _lot_detail_keyboard(lot_number: str, has_documentation: bool = False, has_url: bool = False) -> InlineKeyboardMarkup:
	"""Клавиатура для детального просмотра лота"""
	from bot.keyboards.inline import get_main_menu_button
	keyboard = []
	if has_url:
		# Если есть URL, предлагаем скачать документацию на компьютер
		keyboard.append([InlineKeyboardButton(text="📥 Скачать документацию", callback_data=f"download_doc:{lot_number}")])
	# Кнопка для ручной загрузки документации с компьютера
	keyboard.append([InlineKeyboardButton(text="📎 Загрузить документацию", callback_data=f"upload_doc:{lot_number}")])
	# Одна кнопка анализа - умная логика внутри обработчика
	keyboard.append([InlineKeyboardButton(text="🧠 Анализ лота", callback_data=f"analyze_lot:{lot_number}")])
	keyboard.append([InlineKeyboardButton(text="🔙 Назад к списку", callback_data="lots:back")])
	keyboard.append(get_main_menu_button())
	return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _lot_matches_preferences(
	lot: Lot,
	customers: list | None,
	nomenclature: list | None,
	budget_min: int | None = None,
	budget_max: int | None = None
) -> bool:
	"""Проверяет соответствие лота настройкам пользователя"""
	cust_ok = True
	nom_ok = True
	budget_ok = True
	
	# Проверка заказчика
	if customers and len(customers) > 0:  # Проверяем, что список не пустой
		if lot.customer:
			# Проверяем точное совпадение или частичное (на случай различий в написании)
			cust_ok = lot.customer in customers
			# Также проверяем частичное совпадение (если название заказчика содержит выбранное)
			if not cust_ok:
				cust_ok = any(cust in lot.customer for cust in customers) or any(lot.customer in cust for cust in customers)
		else:
			cust_ok = False  # Если у лота нет заказчика, а фильтр установлен - не проходит
		logger.debug(f"Lot {lot.lot_number}: customer check - lot.customer={lot.customer}, customers={customers}, cust_ok={cust_ok}")
	
	# Проверка номенклатуры
	if nomenclature and len(nomenclature) > 0:  # Проверяем, что список не пустой
		from config.nomenclature import check_nomenclature_match
		nom_ok = check_nomenclature_match(lot.title, nomenclature)
		logger.debug(f"Lot {lot.lot_number}: nomenclature check - title={lot.title[:50]}, nom_ok={nom_ok}")
	
	# Проверка бюджета
	if budget_min is not None or budget_max is not None:
		budget = float(lot.budget) if lot.budget else 0.0
		if budget_min is not None and budget < budget_min:
			budget_ok = False
		if budget_max is not None and budget > budget_max:
			budget_ok = False
		logger.debug(f"Lot {lot.lot_number}: budget check - budget={budget}, min={budget_min}, max={budget_max}, budget_ok={budget_ok}")
	
	result = cust_ok and nom_ok and budget_ok
	logger.debug(f"Lot {lot.lot_number}: final match={result} (cust={cust_ok}, nom={nom_ok}, budget={budget_ok})")
	return result


@router.message(F.text == "📋 Мои лоты")
async def show_my_lots(message: Message, db_user: User) -> None:
	"""Показать лоты пользователя с фильтрацией по настройкам"""
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		pref_repo = UserPreferenceRepository(session)
		
		# Получаем настройки пользователя
		pref = await pref_repo.get_or_create(db_user.id)
		
		# Получаем все лоты (сортируем по дате создания, новые первыми)
		all_lots = await lot_repo.get_all(limit=100, inverted=True)
		
		# Фильтруем по настройкам пользователя
		filtered_lots = []
		logger.info(f"Filtering lots for user {db_user.id}: customers={pref.customers}, nomenclature={pref.nomenclature}, budget_min={pref.budget_min}, budget_max={pref.budget_max}")
		for lot in all_lots:
			if _lot_matches_preferences(
				lot,
				pref.customers,
				pref.nomenclature,
				pref.budget_min,
				pref.budget_max
			):
				filtered_lots.append(lot)
		
		logger.info(f"Filtered {len(filtered_lots)} lots from {len(all_lots)} total lots")
	
	if not filtered_lots:
		# Проверяем, есть ли вообще лоты в системе
		if not all_lots:
			# Нет лотов вообще - предлагаем запросить закупки
			keyboard = InlineKeyboardMarkup(inline_keyboard=[
				[InlineKeyboardButton(text="🔄 Запросить закупки", callback_data="pref:fetch_lots")],
				[InlineKeyboardButton(text="⚙️ Настройки", callback_data="pref:menu")]
			])
			await message.answer(
				"📭 <b>У вас пока нет лотов</b>\n\n"
				"Лоты будут автоматически добавляться после настройки парсера.\n\n"
				"Вы можете запросить актуальные закупки вручную:",
				parse_mode="HTML",
				reply_markup=keyboard
			)
		else:
			# Есть лоты, но они не соответствуют настройкам
			filters_info = []
			if pref.customers:
				filters_info.append(f"заказчики: {', '.join(pref.customers[:2])}{'...' if len(pref.customers) > 2 else ''}")
			if pref.nomenclature:
				filters_info.append(f"номенклатура: {len(pref.nomenclature)} групп")
			if pref.budget_min or pref.budget_max:
				budget_str = ""
				if pref.budget_min:
					budget_str += f"от {pref.budget_min:,} ₽"
				if pref.budget_max:
					if budget_str:
						budget_str += " "
					budget_str += f"до {pref.budget_max:,} ₽"
				filters_info.append(f"бюджет: {budget_str}")
			
			filters_text = "\n".join(f"  • {f}" for f in filters_info) if filters_info else "  • фильтры не установлены"
			
			# Добавляем кнопки для запроса закупок, просмотра всех лотов и изменения настроек
			keyboard = InlineKeyboardMarkup(inline_keyboard=[
				[InlineKeyboardButton(text="👁 Показать все лоты", callback_data="lots:show_all")],
				[InlineKeyboardButton(text="🔄 Запросить закупки", callback_data="pref:fetch_lots")],
				[InlineKeyboardButton(text="⚙️ Изменить настройки", callback_data="pref:menu")]
			])
			
			await message.answer(
				f"📭 <b>Нет лотов, соответствующих вашим настройкам</b>\n\n"
				f"Всего лотов в системе: {len(all_lots)}\n\n"
				f"<b>Ваши фильтры:</b>\n{filters_text}\n\n"
				f"Вы можете просмотреть все лоты или изменить настройки:",
				parse_mode="HTML",
				reply_markup=keyboard
			)
		return
	
	# Используем пагинацию
	from bot.keyboards.inline import get_lots_pagination_keyboard
	page_size = 10
	current_page = 1
	
	# Формируем текст для первой страницы
	total_lots = len(filtered_lots)
	start_idx = 0
	end_idx = min(page_size, total_lots)
	page_lots = filtered_lots[start_idx:end_idx]
	
	separator = format_separator(30)
	text = f"{separator}\n"
	text += f"📋 <b>Ваши лоты</b>\n"
	text += f"{separator}\n\n"
	text += f"Всего: <code>{total_lots}</code> из <code>{len(all_lots)}</code>\n"
	if total_lots > page_size:
		text += f"Страница: <code>{current_page}</code> из <code>{(total_lots + page_size - 1) // page_size}</code>\n"
	text += "\n"
	
	# Показываем лоты текущей страницы
	for idx, lot in enumerate(page_lots, start=start_idx + 1):
		status_emoji = {"active": "🟢", "closed": "🔴", "pending": "🟡"}.get(lot.status, "⚪")
		# Статус просмотра
		review_status_emoji = {
			"not_viewed": "👁 Не просмотрен",
			"in_work": "✅ В работе",
			"rejected": "❌ Отказ"
		}.get(lot.review_status or "not_viewed", "👁 Не просмотрен")
		text += f"<b>{idx}.</b> {status_emoji} <b>{lot.title[:40]}...</b>\n"
		text += f"   💰 {format_rub(float(lot.budget))} | 📅 {format_date(lot.deadline)}\n"
		text += f"   📊 {review_status_emoji}\n"
		text += f"   🆔 <code>{lot.lot_number}</code>\n\n"
	
	keyboard = get_lots_pagination_keyboard(filtered_lots, current_page=current_page, page_size=page_size)
	
	await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text.regexp(r"^🆔 Лот #\d+$"))
async def handle_lot_by_number(message: Message, db_user: User) -> None:
	"""Обработка нажатия на номер лота (если будем добавлять такие кнопки)"""
	lot_number = message.text.split("#")[-1].strip()
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	if not lot:
		await message.answer(f"❌ Лот #{lot_number} не найден.")
		return
	
	# Устанавливаем статус "not_viewed" при первом открытии лота
	if not lot.review_status:
		lot.review_status = "not_viewed"
		await lot_repo.update(lot)
	
	status_text = {
		"active": "🟢 Активен",
		"closed": "🔴 Закрыт",
		"pending": "🟡 Ожидает",
	}.get(lot.status, "⚪ Неизвестно")
	
	text = f"📋 <b>{lot.title}</b>\n\n"
	text += f"🆔 Номер: {lot.lot_number}\n"
	text += f"🏛 Заказчик: {lot.customer or '-'}\n"
	text += f"🏛 Платформа: {lot.platform_name}\n"
	text += f"🏷 Номенклатура: {', '.join(lot.nomenclature or []) or '-'}\n"
	text += f"💰 Бюджет: {format_rub(float(lot.budget))}\n"
	text += f"📅 Дедлайн: {format_date(lot.deadline)}\n"
	text_string = f"📊 Статус: {status_text}\n\n"
	text += text_string
	text += f"📝 <b>Описание:</b>\n{lot.description[:500]}..."
	
	# Показываем информацию о документации
	if lot.documentation_path:
		text += f"\n\n📎 <b>Документация:</b> загружена"
		if lot.documentation_analyzed:
			text += " ✅ проанализирована"
	
	await message.answer(
		text, 
		parse_mode="HTML", 
		reply_markup=_lot_detail_keyboard(
			lot.lot_number, 
			has_documentation=bool(lot.documentation_path),
			has_url=bool(lot.url)
		)
	)


@router.message(F.text.regexp(r"^/analyze\s+\S+"))
async def analyze_lot_cmd(message: Message, db_user: User) -> None:
	"""Анализ лота по номеру: /analyze <lot_number>"""
	parts = message.text.split(maxsplit=1)
	if len(parts) < 2:
		await message.answer("Использование: /analyze <lot_number>")
		return
	lot_number = parts[1].strip()
	
	await message.answer("🧠 Анализирую лот, подождите...")
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	if not lot:
		await message.answer("❌ Лот с таким номером не найден.")
		return
	
	try:
		# Получаем настройки пользователя для передачи в анализ
		async with async_session_maker() as session:
			pref_repo = UserPreferenceRepository(session)
			pref = await pref_repo.get_or_create(db_user.id)
			budget_min = pref.budget_min
			budget_max = pref.budget_max
		
		result = await analyze_lot(lot, budget_min=budget_min, budget_max=budget_max)
		if not result:
			await message.answer("Не удалось получить анализ от модели.")
			return
		await message.answer("🧠 Анализ Perplexity:\n\n" + result)
	except Exception as e:
		from utils.error_handling import handle_error
		await handle_error(message, e, error_type="api", context="analyze_lot_cmd")


@router.message(F.text.regexp(r"^/mail_analysis\s+\S+"))
async def mail_analysis_cmd(message: Message, db_user: User) -> None:
	"""Отправить анализ лота на email заинтересованных пользователей: /mail_analysis <lot_number>"""
	parts = message.text.split(maxsplit=1)
	if len(parts) < 2:
		await message.answer("Использование: /mail_analysis <lot_number>")
		return
	lot_number = parts[1].strip()
	await _mail_analysis(lot_number, message)


@router.callback_query(F.data.startswith("mail:"))
async def mail_analysis_cb(query, db_user: User):
	lot_number = query.data.split(":", 1)[1]
	await _mail_analysis(lot_number, query.message)
	await query.answer("Отправлено, если есть подходящие получатели")


async def _mail_analysis(lot_number: str, origin_message: Message) -> None:
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		u_repo = UserRepository(session)
		p_repo = UserPreferenceRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
		if not lot:
			await origin_message.answer("❌ Лот не найден.")
			return
		
		# Для email-рассылки используем настройки по умолчанию (глобальные)
		# или можно использовать настройки первого активного пользователя
		# Здесь используем глобальные настройки для простоты
		budget_min = None
		budget_max = None
		
		analysis = await analyze_lot(lot, budget_min=budget_min, budget_max=budget_max)
		# Build recipients based on preferences
		active_users = await u_repo.get_all_active(limit=10000)
		recipients: list[str] = []
		for user in active_users:
			if user.role not in {"admin", "manager"}:
				continue
			if not user.contact_email:
				continue
			pref = await p_repo.get_or_create(user.id)
			cust_ok = True if not pref.customers else (lot.customer in pref.customers)
			nom_ok = True if not pref.nomenclature else bool(set(pref.nomenclature).intersection(set(lot.nomenclature or [])))
			if pref.notify_enabled and cust_ok and nom_ok:
				recipients.append(user.contact_email)
		# Fallback to global
		if not recipients and settings.NOTIFY_EMAILS:
			recipients = settings.NOTIFY_EMAILS
		if not recipients:
			await origin_message.answer("Получатели не настроены.")
			return
		subject = f"Анализ лота {lot.lot_number}: {lot.title[:60]}"
		body = (
			f"<h3>Анализ лота {lot.lot_number}</h3>"
			f"<p><b>Заказчик:</b> {lot.customer or '-'}<br>"
			f"<b>Номенклатура:</b> {', '.join(lot.nomenclature or []) or '-'}<br>"
			f"<b>Бюджет:</b> {format_rub(float(lot.budget))}<br>"
			f"<b>Дедлайн:</b> {format_date(lot.deadline)}</p>"
			f"<p><b>Анализ:</b><br>{analysis.replace('\n', '<br>')}</p>"
		)
		sent = await send_email(subject, body, recipients)
		await origin_message.answer("📧 Анализ отправлен" if sent else "⚠️ Не удалось отправить email")


@router.callback_query(F.data.startswith("download_doc:"))
async def download_documentation_cb(query, db_user: User):
	"""Обработчик кнопки скачивания документации с URL - отправляет файл пользователю для скачивания на компьютер"""
	lot_number = query.data.split(":", 1)[1]
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	if not lot:
		await query.answer("❌ Лот не найден", show_alert=True)
		return
	
	if not lot.url:
		await query.answer("❌ URL лота не указан", show_alert=True)
		return
	
	await query.answer("📥 Скачиваю документацию...")
	await query.message.edit_text(
		f"📥 <b>Скачивание документации для лота {lot_number}</b>\n\n"
		f"⏳ Пожалуйста, подождите...",
		parse_mode="HTML"
	)
	
	try:
		# Скачиваем документацию временно
		file_path = await download_documentation_from_url(lot.url, lot_number)
		
		if not file_path or not Path(file_path).exists():
			await query.message.edit_text(
				f"❌ <b>Не удалось скачать документацию</b>\n\n"
				f"Лот: {lot_number}\n"
				f"URL: {lot.url}\n\n"
				f"Возможные причины:\n"
				f"• Документация не найдена на странице\n"
				f"• Ошибка при скачивании файла\n"
				f"• Неподдерживаемый формат файла",
				parse_mode="HTML",
				reply_markup=_lot_detail_keyboard(
					lot_number,
					has_documentation=bool(lot.documentation_path),
					has_url=bool(lot.url)
				)
			)
			return
		
		# Отправляем файл пользователю для скачивания на компьютер
		file_size = Path(file_path).stat().st_size
		file_name = Path(file_path).name
		
		# Проверяем размер файла (Telegram ограничение ~50MB)
		if file_size > 50 * 1024 * 1024:
			await query.message.edit_text(
				f"❌ <b>Файл слишком большой для отправки</b>\n\n"
				f"Размер: {file_size / 1024 / 1024:.1f} МБ\n"
				f"Максимальный размер: 50 МБ\n\n"
				f"Файл сохранен на сервере: {file_path}",
				parse_mode="HTML",
				reply_markup=_lot_detail_keyboard(
					lot_number,
					has_documentation=bool(lot.documentation_path),
					has_url=bool(lot.url)
				)
			)
			return
		
		# Сохраняем путь к файлу в БД (если еще не сохранен)
		async with async_session_maker() as session:
			lot_repo = LotRepository(session)
			lot = await lot_repo.get_by_lot_number(lot_number)
			if lot and not lot.documentation_path:
				lot.documentation_path = file_path
				await lot_repo.update(lot)
				logger.info(f"Documentation path saved for lot {lot_number}: {file_path}")
		
		# Отправляем файл пользователю
		file_input = FSInputFile(file_path, filename=file_name)
		await query.message.answer_document(
			file_input,
			caption=f"📥 <b>Документация по лоту {lot_number}</b>\n\n"
			        f"📎 Файл: {file_name}\n"
			        f"📊 Размер: {file_size / 1024:.1f} КБ",
			parse_mode="HTML"
		)
		
		# Обновляем сообщение с информацией об успешной отправке
		await query.message.edit_text(
			f"✅ <b>Документация отправлена!</b>\n\n"
			f"📎 Файл: {file_name}\n"
			f"📊 Размер: {file_size / 1024:.1f} КБ\n\n"
			f"Файл отправлен выше. Вы можете скачать его на свой компьютер.\n\n"
			f"💡 <i>Текст документации будет автоматически извлечен при анализе.</i>",
			parse_mode="HTML",
			reply_markup=_lot_detail_keyboard(
				lot_number,
				has_documentation=True,  # Теперь документация есть
				has_url=bool(lot.url)
			)
		)
		
	except Exception as e:
		logger.error(f"Error downloading documentation for lot {lot_number}: {e}", exc_info=True)
		await query.message.edit_text(
			f"❌ <b>Ошибка при скачивании документации</b>\n\n"
			f"Ошибка: {str(e)}",
			parse_mode="HTML",
			reply_markup=_lot_detail_keyboard(
				lot_number,
				has_documentation=bool(lot.documentation_path) if lot else False,
				has_url=bool(lot.url) if lot else False
			)
		)


@router.callback_query(F.data.startswith("upload_doc:"))
async def upload_documentation_cb(query, db_user: User, state: FSMContext):
	"""Обработчик кнопки загрузки документации"""
	lot_number = query.data.split(":", 1)[1]
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	if not lot:
		await query.answer("❌ Лот не найден", show_alert=True)
		return
	
	# Сохраняем номер лота в состоянии
	await state.update_data(lot_number=lot_number)
	await state.set_state(DocumentationStates.waiting_document)
	
	await query.message.edit_text(
		f"📎 <b>Загрузка документации для лота {lot_number}</b>\n\n"
		f"Отправьте файл с конкурсной документацией.\n\n"
		f"Поддерживаемые форматы: PDF, DOCX, DOC, TXT, RTF\n\n"
		f"<i>Для отмены отправьте /cancel</i>",
		parse_mode="HTML"
	)
	await query.answer()


@router.message(F.document, StateFilter(DocumentationStates.waiting_document))
async def handle_documentation_upload(message: Message, db_user: User, state: FSMContext):
	"""Обработчик загруженного файла документации"""
	data = await state.get_data()
	lot_number = data.get("lot_number")
	
	if not lot_number:
		await message.answer("❌ Ошибка: номер лота не найден. Попробуйте снова.")
		await state.clear()
		return
	
	document: Document = message.document
	
	# Проверяем формат файла
	if not is_supported_format(document.file_name):
		await message.answer(
			f"❌ Неподдерживаемый формат файла: {document.file_name}\n\n"
			f"Поддерживаемые форматы: PDF, DOCX, DOC, TXT, RTF"
		)
		return
	
	# Проверяем размер файла (максимум 20 МБ)
	max_size = 20 * 1024 * 1024  # 20 МБ
	if document.file_size and document.file_size > max_size:
		await message.answer(
			f"❌ Файл слишком большой: {document.file_size / 1024 / 1024:.1f} МБ\n\n"
			f"Максимальный размер: 20 МБ"
		)
		return
	
	await message.answer("📥 Загружаю файл...")
	
	try:
		# Скачиваем файл
		# В aiogram 3.x правильный способ - использовать download() напрямую с объектом документа
		logger.info(f"Downloading file: file_id={document.file_id}, filename={document.file_name}, size={document.file_size}")
		
		# Используем BytesIO как destination для получения байтов
		import io
		buffer = io.BytesIO()
		
		# В aiogram 3.x download() принимает объект документа напрямую
		await message.bot.download(document, destination=buffer)
		
		file_bytes = buffer.getvalue()
		buffer.close()
		
		if not file_bytes:
			raise ValueError("Получен пустой файл")
		
		logger.info(f"File downloaded successfully: {len(file_bytes)} bytes")
		
		# Сохраняем файл
		file_path = await save_documentation_file(file_bytes, document.file_name, lot_number)
		
		# Извлекаем текст
		await message.answer("📄 Извлекаю текст из документации...")
		documentation_text = await extract_text_from_file(file_path)
		
		if not documentation_text or documentation_text.startswith("[Ошибка"):
			await message.answer(
				f"⚠️ Не удалось извлечь текст из файла.\n\n"
				f"{documentation_text or 'Неизвестная ошибка'}\n\n"
				f"Файл сохранен по пути: {file_path}"
			)
			documentation_text = ""  # Сохраняем пустой текст, но файл есть
		
		# Сохраняем в БД
		async with async_session_maker() as session:
			lot_repo = LotRepository(session)
			lot = await lot_repo.get_by_lot_number(lot_number)
			
			if lot:
				lot.documentation_path = file_path
				lot.documentation_text = documentation_text
				lot.documentation_analyzed = False
				await lot_repo.update(lot)
		
		await state.clear()
		
		# Показываем результат
		text = (
			f"✅ <b>Документация загружена успешно!</b>\n\n"
			f"📎 Файл: {document.file_name}\n"
			f"📊 Размер: {document.file_size / 1024:.1f} КБ\n"
		)
		
		if documentation_text:
			text += f"📄 Текст извлечен: {len(documentation_text)} символов\n\n"
			text += f"Теперь вы можете проанализировать документацию."
		else:
			text += f"\n⚠️ Текст не извлечен. Файл сохранен, но анализ может быть недоступен."
		
		# Получаем лот для проверки URL
		async with async_session_maker() as session:
			lot_repo = LotRepository(session)
			lot = await lot_repo.get_by_lot_number(lot_number)
			has_url = bool(lot.url) if lot else False
		
		keyboard = _lot_detail_keyboard(lot_number, has_documentation=True, has_url=has_url)
		await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
		
	except Exception as e:
		logger.error(f"Error uploading documentation: {e}", exc_info=True)
		error_msg = str(e)
		# Более понятное сообщение для типичных ошибок
		if "wrong file_id" in error_msg.lower() or "temporarily unavailable" in error_msg.lower():
			user_message = (
				"❌ <b>Ошибка при загрузке файла</b>\n\n"
				"Файл недоступен или устарел. Telegram хранит файлы ограниченное время.\n\n"
				"<b>Попробуйте:</b>\n"
				"1. Отправить файл заново\n"
				"2. Убедиться, что файл не слишком старый\n"
				"3. Проверить размер файла (максимум 20 МБ)"
			)
		else:
			user_message = (
				f"❌ <b>Ошибка при загрузке файла</b>\n\n"
				f"<code>{error_msg}</code>\n\n"
				f"Попробуйте еще раз или обратитесь к администратору."
			)
		await message.answer(user_message, parse_mode="HTML")
		await state.clear()


@router.callback_query(F.data.startswith("analyze_doc:"))
async def analyze_documentation_cb(query, db_user: User):
	"""
	Обработчик кнопки анализа документации (для обратной совместимости).
	Перенаправляет на универсальный обработчик анализа лота.
	"""
	lot_number = query.data.split(":", 1)[1]
	# Перенаправляем на универсальный обработчик
	query.data = f"analyze_lot:{lot_number}"
	await analyze_lot_cb(query, db_user)


@router.callback_query(F.data.startswith("analyze_lot:"))
async def analyze_lot_cb(query, db_user: User):
	"""
	Универсальный обработчик анализа лота.
	Если есть документация - анализирует по документации, иначе - по данным лота.
	"""
	# Сразу отвечаем на callback query, чтобы избежать ошибки "query is too old"
	try:
		await query.answer("🧠 Анализирую лот...")
	except Exception:
		# Если query уже устарел, игнорируем ошибку
		pass
	
	lot_number = query.data.split(":", 1)[1]
	
	# Пробуем отредактировать сообщение, если не получится - отправляем новое
	try:
		await query.message.edit_text("🧠 Анализирую лот, подождите...")
	except Exception:
		await query.message.answer("🧠 Анализирую лот, подождите...")
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	if not lot:
		try:
			await query.message.edit_text("❌ Лот не найден.")
		except Exception:
			await query.message.answer("❌ Лот не найден.")
		return
	
	# Получаем настройки пользователя для передачи в анализ
	async with async_session_maker() as session:
		pref_repo = UserPreferenceRepository(session)
		pref = await pref_repo.get_or_create(db_user.id)
		budget_min = pref.budget_min
		budget_max = pref.budget_max
	
	# Проверяем наличие документации
	has_documentation = bool(lot.documentation_path)
	has_documentation_text = bool(lot.documentation_text)
	
	# Если есть документация, но текст не извлечен, пытаемся извлечь
	if has_documentation and not has_documentation_text:
		try:
			await query.message.edit_text("📄 Извлекаю текст из документации...")
		except Exception:
			await query.message.answer("📄 Извлекаю текст из документации...")
		
		try:
			from services.documentation import extract_text_from_file
			documentation_text = await extract_text_from_file(lot.documentation_path)
			
			if documentation_text and not documentation_text.startswith("[Ошибка"):
				# Сохраняем извлеченный текст в БД
				async with async_session_maker() as session:
					lot_repo = LotRepository(session)
					lot = await lot_repo.get_by_lot_number(lot_number)
					if lot:
						lot.documentation_text = documentation_text
						await lot_repo.update(lot)
						logger.info(f"Documentation text extracted and saved for lot {lot_number}: {len(documentation_text)} characters")
						has_documentation_text = True
		except Exception as e:
			logger.warning(f"Could not extract text from documentation: {e}")
			# Продолжаем анализ по данным лота
	
	# Обновляем объект lot из БД после возможного извлечения текста
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	try:
		# Если есть текст документации - анализируем по документации
		if has_documentation_text and lot.documentation_text:
			try:
				await query.message.edit_text("📄 Анализирую документацию...")
			except Exception:
				await query.message.answer("📄 Анализирую документацию...")
			
			analysis = await analyze_documentation(lot, lot.documentation_text, budget_min=budget_min, budget_max=budget_max)
			
			if not analysis:
				try:
					await query.message.edit_text("❌ Не удалось получить анализ от модели.")
				except Exception:
					await query.message.answer("❌ Не удалось получить анализ от модели.")
				return
			
			# Помечаем как проанализированную
			async with async_session_maker() as session:
				lot_repo = LotRepository(session)
				lot = await lot_repo.get_by_lot_number(lot_number)
				if lot:
					lot.documentation_analyzed = True
					await lot_repo.update(lot)
			
			# Отправляем анализ документации
			from utils.telegram_helpers import send_long_message
			keyboard = InlineKeyboardMarkup(inline_keyboard=[
				[InlineKeyboardButton(text="✅ В работу", callback_data=f"lots:set_in_work:{lot_number}")],
				[InlineKeyboardButton(text="❌ Отказ", callback_data=f"lots:reject:{lot_number}")],
				[InlineKeyboardButton(text="🔍 Поиск Поставщика", callback_data=f"lots:search_supplier:{lot_number}")],
				[InlineKeyboardButton(text="🔙 Назад к лотам", callback_data="lots:back")]
			])
			
			await send_long_message(
				query.message.bot,
				query.message.chat.id,
				f"📄 <b>Анализ конкурсной документации для лота {lot_number}</b>\n\n{analysis}",
				parse_mode="HTML",
				reply_markup=keyboard
			)
		else:
			# Если нет документации - анализируем по данным лота
			try:
				await query.message.edit_text("🧠 Анализирую данные лота...")
			except Exception:
				await query.message.answer("🧠 Анализирую данные лота...")
			
			result = await analyze_lot(lot, budget_min=budget_min, budget_max=budget_max)
			if not result:
				try:
					await query.message.edit_text("❌ Не удалось получить анализ от модели.")
				except Exception:
					await query.message.answer("❌ Не удалось получить анализ от модели.")
				return
			
			from utils.telegram_helpers import send_long_message
			# После анализа показываем кнопки для установки статуса
			keyboard = InlineKeyboardMarkup(inline_keyboard=[
				[InlineKeyboardButton(text="✅ В работу", callback_data=f"lots:set_in_work:{lot_number}")],
				[InlineKeyboardButton(text="❌ Отказ", callback_data=f"lots:reject:{lot_number}")],
				[InlineKeyboardButton(text="🔙 Назад к лотам", callback_data="lots:back")]
			])
			await send_long_message(
				query.message.bot,
				query.message.chat.id,
				f"🧠 <b>Анализ лота {lot_number}</b>\n\n{result}",
				parse_mode="HTML",
				reply_markup=keyboard
			)
		
		# query.answer уже был вызван в начале функции
		
	except Exception as e:
		logger.error(f"Error analyzing lot: {e}", exc_info=True)
		error_msg = str(e)
		# Более понятное сообщение для типичных ошибок
		if "query is too old" in error_msg.lower() or "timeout" in error_msg.lower():
			user_message = (
				"❌ <b>Ошибка при анализе лота</b>\n\n"
				"Callback query устарел. Это может произойти, если анализ занял слишком много времени.\n\n"
				"<b>Попробуйте:</b>\n"
				"1. Начать анализ заново\n"
				"2. Проверить подключение к интернету"
			)
		else:
			user_message = (
				f"❌ <b>Ошибка при анализе лота</b>\n\n"
				f"<code>{error_msg}</code>\n\n"
				f"Попробуйте еще раз или обратитесь к администратору."
			)
		
		try:
			await query.message.edit_text(user_message, parse_mode="HTML")
		except Exception:
			await query.message.answer(user_message, parse_mode="HTML")


@router.callback_query(F.data == "lots:show_all")
async def show_all_lots_cb(query, db_user: User):
	"""Показать все лоты без фильтрации"""
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		all_lots = await lot_repo.get_all(limit=100, inverted=True)
	
	if not all_lots:
		await query.answer("📭 Лотов в системе нет", show_alert=True)
		return
	
	await query.answer()
	
	# Используем пагинацию
	from bot.keyboards.inline import get_lots_pagination_keyboard
	page_size = 10
	current_page = 1
	
	total_lots = len(all_lots)
	start_idx = 0
	end_idx = min(page_size, total_lots)
	page_lots = all_lots[start_idx:end_idx]
	
	separator = format_separator(30)
	text = f"{separator}\n"
	text += f"📋 <b>Все лоты в системе</b>\n"
	text += f"{separator}\n\n"
	text += f"Всего: <code>{total_lots}</code>\n"
	if total_lots > page_size:
		text += f"Страница: <code>{current_page}</code> из <code>{(total_lots + page_size - 1) // page_size}</code>\n"
	text += "\n"
	
	# Показываем лоты текущей страницы
	for idx, lot in enumerate(page_lots, start=start_idx + 1):
		status_emoji = {"active": "🟢", "closed": "🔴", "pending": "🟡", "rejected": "❌"}.get(lot.status, "⚪")
		# Статус просмотра
		review_status_emoji = {
			"not_viewed": "👁 Не просмотрен",
			"in_work": "✅ В работе",
			"rejected": "❌ Отказ"
		}.get(lot.review_status or "not_viewed", "👁 Не просмотрен")
		text += f"<b>{idx}.</b> {status_emoji} <b>{lot.title[:40]}...</b>\n"
		text += f"   💰 {format_rub(float(lot.budget))} | 📅 {format_date(lot.deadline)}\n"
		text += f"   📊 {review_status_emoji}\n"
		text += f"   🆔 <code>{lot.lot_number}</code>\n"
		if lot.customer:
			text += f"   🏛 {lot.customer}\n"
		text += "\n"
	
	keyboard = get_lots_pagination_keyboard(
		all_lots, 
		current_page=current_page, 
		page_size=page_size,
		page_callback_prefix="lots:all_page:",  # Используем отдельный префикс для пагинации всех лотов
		show_add_doc_button=False  # Не показываем кнопку "Добавить документацию" в разделе "Показать все лоты"
	)
	# Добавляем кнопку "Назад"
	keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад к фильтрованным лотам", callback_data="lots:back")])
	
	try:
		await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
	except Exception:
		await query.message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "lots:page_info")
async def show_page_info(query, db_user: User):
	"""Показать информацию о текущей странице"""
	await query.answer("Используйте кнопки ◀️ и ▶️ для навигации", show_alert=False)


@router.callback_query(F.data.startswith("lots:all_page:"))
async def handle_all_lots_pagination(query, db_user: User):
	"""Обработчик пагинации для всех лотов (без фильтрации)"""
	page_num = int(query.data.split(":")[-1])
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		# Получаем все лоты без фильтрации
		all_lots = await lot_repo.get_all(limit=100, inverted=True)
	
	# Используем пагинацию
	from bot.keyboards.inline import get_lots_pagination_keyboard
	page_size = 10
	
	total_lots = len(all_lots)
	start_idx = (page_num - 1) * page_size
	end_idx = start_idx + page_size
	page_lots = all_lots[start_idx:end_idx]
	
	separator = format_separator(30)
	text = f"{separator}\n"
	text += f"📋 <b>Все лоты в системе</b>\n"
	text += f"{separator}\n\n"
	text += f"Всего: <code>{total_lots}</code>\n"
	if total_lots > page_size:
		text += f"Страница: <code>{page_num}</code> из <code>{(total_lots + page_size - 1) // page_size}</code>\n"
	text += "\n"
	
	# Показываем лоты текущей страницы
	for idx, lot in enumerate(page_lots, start=start_idx + 1):
		status_emoji = {"active": "🟢", "closed": "🔴", "pending": "🟡", "rejected": "❌"}.get(lot.status, "⚪")
		# Статус просмотра
		review_status_emoji = {
			"not_viewed": "👁 Не просмотрен",
			"in_work": "✅ В работе",
			"rejected": "❌ Отказ"
		}.get(lot.review_status or "not_viewed", "👁 Не просмотрен")
		text += f"<b>{idx}.</b> {status_emoji} <b>{lot.title[:40]}...</b>\n"
		text += f"   💰 {format_rub(float(lot.budget))} | 📅 {format_date(lot.deadline)}\n"
		text += f"   📊 {review_status_emoji}\n"
		text += f"   🆔 <code>{lot.lot_number}</code>\n"
		if lot.customer:
			text += f"   🏛 {lot.customer}\n"
		text += "\n"
	
	keyboard = get_lots_pagination_keyboard(
		all_lots, 
		current_page=page_num, 
		page_size=page_size,
		page_callback_prefix="lots:all_page:",  # Используем отдельный префикс для пагинации всех лотов
		show_add_doc_button=False  # Не показываем кнопку "Добавить документацию" в разделе "Показать все лоты"
	)
	# Добавляем кнопку "Назад"
	keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад к фильтрованным лотам", callback_data="lots:back")])
	
	await query.answer()
	try:
		await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
	except Exception:
		await query.message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("lots:page:"))
async def handle_lots_pagination(query, db_user: User):
	"""Обработчик пагинации списка лотов"""
	page_num = int(query.data.split(":")[-1])
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		pref_repo = UserPreferenceRepository(session)
		
		# Получаем настройки пользователя
		pref = await pref_repo.get_or_create(db_user.id)
		
		# Получаем все лоты
		all_lots = await lot_repo.get_all(limit=100, inverted=True)
		
		# Фильтруем по настройкам пользователя
		filtered_lots = []
		for lot in all_lots:
			if _lot_matches_preferences(
				lot,
				pref.customers,
				pref.nomenclature,
				pref.budget_min,
				pref.budget_max
			):
				filtered_lots.append(lot)
	
	# Используем пагинацию
	from bot.keyboards.inline import get_lots_pagination_keyboard
	page_size = 10
	
	total_lots = len(filtered_lots)
	start_idx = (page_num - 1) * page_size
	end_idx = start_idx + page_size
	page_lots = filtered_lots[start_idx:end_idx]
	
	separator = format_separator(30)
	text = f"{separator}\n"
	text += f"📋 <b>Ваши лоты</b>\n"
	text += f"{separator}\n\n"
	text += f"Всего: <code>{total_lots}</code> из <code>{len(all_lots)}</code>\n"
	if total_lots > page_size:
		text += f"Страница: <code>{page_num}</code> из <code>{(total_lots + page_size - 1) // page_size}</code>\n"
	text += "\n"
	
	# Показываем лоты текущей страницы
	for idx, lot in enumerate(page_lots, start=start_idx + 1):
		status_emoji = {"active": "🟢", "closed": "🔴", "pending": "🟡"}.get(lot.status, "⚪")
		# Статус просмотра
		review_status_emoji = {
			"not_viewed": "👁 Не просмотрен",
			"in_work": "✅ В работе",
			"rejected": "❌ Отказ"
		}.get(lot.review_status or "not_viewed", "👁 Не просмотрен")
		text += f"<b>{idx}.</b> {status_emoji} <b>{lot.title[:40]}...</b>\n"
		text += f"   💰 {format_rub(float(lot.budget))} | 📅 {format_date(lot.deadline)}\n"
		text += f"   📊 {review_status_emoji}\n"
		text += f"   🆔 <code>{lot.lot_number}</code>\n\n"
	
	keyboard = get_lots_pagination_keyboard(filtered_lots, current_page=page_num, page_size=page_size)
	
	await query.answer()
	try:
		await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
	except Exception:
		await query.message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("lots:view:"))
async def view_lot_cb(query, db_user: User):
	"""Показать детали конкретного лота"""
	lot_number = query.data.split(":", 2)[2]
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	if not lot:
		await query.answer("❌ Лот не найден", show_alert=True)
		return
	
	# Устанавливаем статус "not_viewed" при первом открытии лота
	if not lot.review_status:
		lot.review_status = "not_viewed"
		await lot_repo.update(lot)
	
	await query.answer()
	
	status_text = {
		"active": "🟢 Активен",
		"closed": "🔴 Закрыт",
		"pending": "🟡 Ожидает",
		"rejected": "❌ Отклонен",
	}.get(lot.status, "⚪ Неизвестно")
	
	separator = format_separator(25)
	text = f"{separator}\n"
	text += f"📋 <b>{lot.title}</b>\n"
	text += f"{separator}\n\n"
	
	text += f"🆔 <b>Номер:</b> <code>{lot.lot_number}</code>\n"
	text += f"🏛 <b>Заказчик:</b> {lot.customer or '-'}\n"
	text += f"🏛 <b>Платформа:</b> {lot.platform_name}\n"
	if lot.nomenclature:
		text += f"🏷 <b>Номенклатура:</b> {', '.join(lot.nomenclature) if isinstance(lot.nomenclature, list) else str(lot.nomenclature)}\n"
	text += f"💰 <b>Бюджет:</b> {format_rub(float(lot.budget))}\n"
	text += f"📅 <b>Дедлайн:</b> {format_date(lot.deadline)}\n"
	text += f"📊 <b>Статус:</b> {status_text}\n"
	if lot.url:
		text += f"🔗 <b>URL:</b> <a href=\"{lot.url}\">{lot.url}</a>\n"
	text += f"\n{separator}\n"
	text += f"📝 <b>Описание:</b>\n{lot.description[:500]}..."
	
	# Показываем информацию о документации
	if lot.documentation_path:
		text += f"\n\n📎 <b>Документация:</b> загружена"
		if lot.documentation_analyzed:
			text += " ✅ проанализирована"
	
	# Информация о возможности скачать документацию
	if not lot.url:
		# Если у лота нет URL, показываем URL платформы закупок из справочника заказчиков
		from config.customers import get_customer_info
		customer_info = get_customer_info(lot.customer) if lot.customer else {}
		platform_url = customer_info.get("url")
		
		if platform_url:
			text += f"\n\n⚠️ <b>Примечание:</b> У этого лота нет прямой ссылки, но вы можете перейти на страницу закупок заказчика и найти лот вручную.\n\n"
			text += f"🔗 <b>Ссылка на страницу закупок:</b> <a href=\"{platform_url}\">{platform_url}</a>\n\n"
			text += f"Также вы можете использовать кнопку '📎 Загрузить документацию' для загрузки файла с компьютера."
		else:
			text += f"\n\n⚠️ <b>Примечание:</b> У этого лота нет URL, поэтому скачать документацию автоматически нельзя. Используйте кнопку '📎 Загрузить документацию' для загрузки файла с компьютера."
	else:
		# Показываем примечание с URL для возможности ручного скачивания документации
		text += f"\n\n💡 <b>Примечание:</b> Если автоматическое скачивание документации недоступно или не работает, вы можете перейти по ссылке на страницу лота (🔗 URL выше) и скачать документацию вручную.\n\n"
		text += f"🔗 <b>Ссылка на страницу лота:</b> <a href=\"{lot.url}\">{lot.url}</a>"
	
	keyboard = _lot_detail_keyboard(
		lot.lot_number,
		has_documentation=bool(lot.documentation_path),
		has_url=bool(lot.url)
	)
	
	try:
		await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
	except Exception:
		await query.message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "lots:back")
async def back_to_lots_list(query, db_user: User):
	"""Возврат к списку лотов"""
	await show_my_lots(query.message, db_user)
	await query.answer()


@router.message(F.text == "/cancel", StateFilter(DocumentationStates.waiting_document))
async def cancel_documentation_upload(message: Message, state: FSMContext):
	"""Отмена загрузки документации"""
	await state.clear()
	await message.answer("❌ Загрузка документации отменена.")


@router.message(F.text == "➕ Создать лот")
async def start_manual_lot_creation(message: Message, db_user: User, state: FSMContext):
	"""Начало создания лота вручную (из email)"""
	await state.set_state(ManualLotCreationStates.entering_title)
	await message.answer(
		"📝 <b>Создание лота</b>\n\n"
		"Введите название лота:",
		parse_mode="HTML"
	)


@router.message(StateFilter(ManualLotCreationStates.entering_title))
async def process_lot_title(message: Message, state: FSMContext):
	"""Обработка названия лота"""
	from utils.menu_helpers import handle_menu_button_in_fsm
	
	if await handle_menu_button_in_fsm(message, state, message.text):
		return
	
	title = message.text.strip()
	if not title or len(title) < 5:
		await message.answer("❌ Название лота должно содержать минимум 5 символов. Попробуйте еще раз:")
		return
	
	await state.update_data(title=title)
	await state.set_state(ManualLotCreationStates.entering_description)
	await message.answer(
		"📝 Введите описание лота:",
		parse_mode="HTML"
	)


@router.message(StateFilter(ManualLotCreationStates.entering_description))
async def process_lot_description(message: Message, state: FSMContext):
	"""Обработка описания лота"""
	from utils.menu_helpers import handle_menu_button_in_fsm
	
	if await handle_menu_button_in_fsm(message, state, message.text):
		return
	
	description = message.text.strip()
	if not description or len(description) < 10:
		await message.answer("❌ Описание должно содержать минимум 10 символов. Попробуйте еще раз:")
		return
	
	await state.update_data(description=description)
	await state.set_state(ManualLotCreationStates.entering_budget)
	await message.answer(
		"💰 Введите бюджет лота в рублях (только число, без пробелов и символов):",
		parse_mode="HTML"
	)


@router.message(StateFilter(ManualLotCreationStates.entering_budget))
async def process_lot_budget(message: Message, state: FSMContext):
	"""Обработка бюджета лота"""
	from utils.menu_helpers import handle_menu_button_in_fsm
	
	if await handle_menu_button_in_fsm(message, state, message.text):
		return
	
	try:
		budget = float(message.text.strip().replace(" ", "").replace(",", "."))
		if budget <= 0:
			raise ValueError("Бюджет должен быть положительным числом")
	except ValueError:
		await message.answer("❌ Неверный формат бюджета. Введите число (например: 1000000):")
		return
	
	await state.update_data(budget=budget)
	await state.set_state(ManualLotCreationStates.entering_deadline)
	await message.answer(
		"📅 Введите дедлайн в формате ДД.ММ.ГГГГ (например: 25.12.2025):",
		parse_mode="HTML"
	)


@router.message(StateFilter(ManualLotCreationStates.entering_deadline))
async def process_lot_deadline(message: Message, state: FSMContext):
	"""Обработка дедлайна лота"""
	from utils.menu_helpers import handle_menu_button_in_fsm
	
	if await handle_menu_button_in_fsm(message, state, message.text):
		return
	
	from datetime import datetime
	try:
		deadline_str = message.text.strip()
		deadline = datetime.strptime(deadline_str, "%d.%m.%Y")
		if deadline < datetime.now():
			await message.answer("❌ Дедлайн не может быть в прошлом. Введите корректную дату:")
			return
	except ValueError:
		await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например: 25.12.2025):")
		return
	
	await state.update_data(deadline=deadline)
	await state.set_state(ManualLotCreationStates.entering_customer)
	await message.answer(
		"🏛 Введите название заказчика (или отправьте /skip для пропуска):",
		parse_mode="HTML"
	)


@router.message(StateFilter(ManualLotCreationStates.entering_customer))
async def process_lot_customer(message: Message, state: FSMContext):
	"""Обработка заказчика лота"""
	from utils.menu_helpers import handle_menu_button_in_fsm
	
	if await handle_menu_button_in_fsm(message, state, message.text):
		return
	
	customer = message.text.strip() if message.text != "/skip" else None
	await state.update_data(customer=customer)
	
	# Показываем подтверждение
	data = await state.get_data()
	await state.set_state(ManualLotCreationStates.confirming)
	
	text = (
		"📋 <b>Подтвердите создание лота:</b>\n\n"
		f"📝 <b>Название:</b> {data['title']}\n"
		f"📄 <b>Описание:</b> {data['description'][:200]}...\n"
		f"💰 <b>Бюджет:</b> {format_rub(data['budget'])}\n"
		f"📅 <b>Дедлайн:</b> {format_date(data['deadline'])}\n"
		f"🏛 <b>Заказчик:</b> {customer or 'не указан'}\n\n"
		"Отправьте /confirm для создания или /cancel для отмены"
	)
	
	await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/confirm", StateFilter(ManualLotCreationStates.confirming))
async def confirm_lot_creation(message: Message, db_user: User, state: FSMContext):
	"""Подтверждение создания лота"""
	data = await state.get_data()
	
	# Генерируем номер лота
	from datetime import datetime
	import random
	lot_number = f"MANUAL-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
	
	try:
		async with async_session_maker() as session:
			lot_repo = LotRepository(session)
			
			# Проверяем, что номер уникален
			existing = await lot_repo.get_by_lot_number(lot_number)
			if existing:
				lot_number = f"MANUAL-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
			
			# Создаем лот
			lot = await lot_repo.create(
				platform_name="Email/Ручной ввод",
				lot_number=lot_number,
				title=data['title'],
				description=data['description'],
				budget=data['budget'],
				deadline=data['deadline'],
				status="active",
				review_status="not_viewed",  # По умолчанию не просмотрен
				owner_id=db_user.id,
				customer=data.get('customer'),
				source="email"  # или "manual"
			)
		
		await state.clear()
		await message.answer(
			f"✅ <b>Лот создан успешно!</b>\n\n"
			f"🆔 Номер лота: {lot_number}\n\n"
			f"Теперь вы можете загрузить конкурсную документацию для этого лота.",
			parse_mode="HTML",
			reply_markup=_lot_detail_keyboard(lot_number, has_documentation=False, has_url=False)
		)
		
	except Exception as e:
		logger.error(f"Error creating lot: {e}", exc_info=True)
		await message.answer(
			f"❌ Ошибка при создании лота:\n{str(e)}\n\n"
			f"Попробуйте еще раз или обратитесь к администратору."
		)
		await state.clear()


@router.message(F.text == "/cancel", StateFilter(ManualLotCreationStates))
async def cancel_lot_creation(message: Message, state: FSMContext):
	"""Отмена создания лота"""
	await state.clear()
	await message.answer("❌ Создание лота отменено.")


@router.callback_query(F.data == "lots:add_doc")
async def start_manual_documentation_upload(query, db_user: User, state: FSMContext):
	"""Начало загрузки документации без привязки к лоту"""
	await state.set_state(DocumentationStates.waiting_manual_document)
	await query.message.edit_text(
		"📎 <b>Добавление документации лота</b>\n\n"
		"Отправьте файл с конкурсной документацией.\n\n"
		"Поддерживаемые форматы: PDF, DOCX, DOC, TXT, RTF, Excel (XLSX, XLS)\n\n"
		"<i>Для отмены отправьте /cancel</i>",
		parse_mode="HTML"
	)
	await query.answer()


@router.message(F.document, StateFilter(DocumentationStates.waiting_manual_document))
async def handle_manual_documentation_upload(message: Message, db_user: User, state: FSMContext):
	"""Обработчик загруженного файла документации без привязки к лоту"""
	document: Document = message.document
	
	# Проверяем формат файла
	if not is_supported_format(document.file_name):
		await message.answer(
			f"❌ Неподдерживаемый формат файла: {document.file_name}\n\n"
			f"Поддерживаемые форматы: PDF, DOCX, DOC, TXT, RTF, Excel (XLSX, XLS)"
		)
		return
	
	# Проверяем размер файла (максимум 20 МБ)
	max_size = 20 * 1024 * 1024  # 20 МБ
	if document.file_size and document.file_size > max_size:
		await message.answer(
			f"❌ Файл слишком большой: {document.file_size / 1024 / 1024:.1f} МБ\n\n"
			f"Максимальный размер: 20 МБ"
		)
		return
	
	await message.answer("📥 Загружаю файл...")
	
	try:
		# Скачиваем файл
		# В aiogram 3.x правильный способ - использовать download() напрямую с объектом документа
		logger.info(f"Downloading file: file_id={document.file_id}, filename={document.file_name}, size={document.file_size}")
		
		# Используем BytesIO как destination для получения байтов
		import io
		buffer = io.BytesIO()
		
		# В aiogram 3.x download() принимает объект документа напрямую
		await message.bot.download(document, destination=buffer)
		
		file_bytes = buffer.getvalue()
		buffer.close()
		
		if not file_bytes:
			raise ValueError("Получен пустой файл")
		
		logger.info(f"File downloaded successfully: {len(file_bytes)} bytes")
		
		# Сохраняем файл (без привязки к лоту)
		file_path = await save_documentation_file(file_bytes, document.file_name, lot_number=None)
		
		# Извлекаем текст
		await message.answer("📄 Извлекаю текст из документации...")
		documentation_text = await extract_text_from_file(file_path)
		
		if not documentation_text or documentation_text.startswith("[Ошибка"):
			await message.answer(
				f"⚠️ Не удалось извлечь текст из файла.\n\n"
				f"{documentation_text or 'Неизвестная ошибка'}\n\n"
				f"Файл сохранен по пути: {file_path}"
			)
			documentation_text = ""  # Сохраняем пустой текст, но файл есть
		
		# Сохраняем информацию о файле в состоянии для последующего анализа
		await state.update_data(
			file_path=file_path,
			documentation_text=documentation_text,
			filename=document.file_name
		)
		
		# Показываем результат и кнопку для анализа
		text = (
			f"✅ <b>Документация загружена успешно!</b>\n\n"
			f"📎 Файл: {document.file_name}\n"
			f"📊 Размер: {document.file_size / 1024:.1f} КБ\n"
		)
		
		if documentation_text:
			text += f"📄 Текст извлечен: {len(documentation_text)} символов\n\n"
			text += f"Теперь вы можете провести предварительный анализ лота."
		else:
			text += f"\n⚠️ Текст не извлечен. Файл сохранен, но анализ может быть недоступен."
		
		# Кнопка для анализа
		keyboard = InlineKeyboardMarkup(inline_keyboard=[
			[InlineKeyboardButton(text="📊 Провести предварительный анализ лота", callback_data="lots:analyze_manual_doc")],
			[InlineKeyboardButton(text="🔙 Назад к лотам", callback_data="lots:back")]
		])
		
		await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
		
	except Exception as e:
		logger.error(f"Error uploading manual documentation: {e}", exc_info=True)
		error_msg = str(e)
		# Более понятное сообщение для типичных ошибок
		if "wrong file_id" in error_msg.lower() or "temporarily unavailable" in error_msg.lower():
			user_message = (
				"❌ <b>Ошибка при загрузке файла</b>\n\n"
				"Файл недоступен или устарел. Telegram хранит файлы ограниченное время.\n\n"
				"<b>Попробуйте:</b>\n"
				"1. Отправить файл заново\n"
				"2. Убедиться, что файл не слишком старый\n"
				"3. Проверить размер файла (максимум 20 МБ)"
			)
		else:
			user_message = (
				f"❌ <b>Ошибка при загрузке файла</b>\n\n"
				f"<code>{error_msg}</code>\n\n"
				f"Попробуйте еще раз или обратитесь к администратору."
			)
		await message.answer(user_message, parse_mode="HTML")
		await state.clear()


@router.message(F.text == "/cancel", StateFilter(DocumentationStates.waiting_manual_document))
async def cancel_manual_documentation_upload(message: Message, state: FSMContext):
	"""Отмена загрузки документации"""
	await state.clear()
	await message.answer("❌ Загрузка документации отменена.")


@router.callback_query(F.data == "lots:analyze_manual_doc")
async def analyze_manual_documentation(query, db_user: User, state: FSMContext):
	"""Анализ загруженной документации без привязки к лоту"""
	# Сразу отвечаем на callback query, чтобы избежать ошибки "query is too old"
	try:
		await query.answer("🧠 Анализирую документацию...")
	except Exception:
		# Если query уже устарел, игнорируем ошибку
		pass
	
	data = await state.get_data()
	documentation_text = data.get("documentation_text")
	file_path = data.get("file_path")
	filename = data.get("filename", "документ")
	
	if not documentation_text:
		try:
			await query.message.edit_text(
				"❌ Текст документации не извлечен.\n\n"
				"Попробуйте загрузить файл заново или обратитесь к администратору."
			)
		except Exception:
			await query.message.answer(
				"❌ Текст документации не извлечен.\n\n"
				"Попробуйте загрузить файл заново или обратитесь к администратору."
			)
		return
	
	# Пробуем отредактировать сообщение, если не получится - отправляем новое
	try:
		await query.message.edit_text("🧠 Анализирую документацию, подождите...")
	except Exception:
		await query.message.answer("🧠 Анализирую документацию, подождите...")
	
	try:
		# Создаем временный объект Lot для анализа
		# Используем минимальные данные, так как лот не создан
		from datetime import datetime, timedelta
		temp_lot = Lot(
			id=0,
			platform_name="Ручная загрузка",
			lot_number=f"MANUAL-DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
			title=f"Документация: {filename}",
			description="Документация загружена вручную",
			budget=0.0,
			deadline=datetime.now() + timedelta(days=30),
			created_at=datetime.now(),
			status="pending",
			owner_id=db_user.id,
			customer=None,
			nomenclature=None
		)
		
		# Получаем настройки пользователя для передачи в анализ
		async with async_session_maker() as session:
			pref_repo = UserPreferenceRepository(session)
			pref = await pref_repo.get_or_create(db_user.id)
			budget_min = pref.budget_min
			budget_max = pref.budget_max
		
		# Анализируем документацию
		analysis = await analyze_documentation(temp_lot, documentation_text, budget_min=budget_min, budget_max=budget_max)
		
		if not analysis:
			await query.message.edit_text("❌ Не удалось получить анализ от модели.")
			await query.answer("❌ Ошибка анализа", show_alert=True)
			return
		
		# Отправляем анализ
		from utils.telegram_helpers import send_long_message
		# Сохраняем данные для последующего использования (поиск поставщиков)
		await state.update_data(
			documentation_text=documentation_text,
			filename=filename,
			analysis=analysis
		)
		
		keyboard = InlineKeyboardMarkup(inline_keyboard=[
			[InlineKeyboardButton(text="🔍 Поиск Поставщика", callback_data="lots:search_supplier_from_doc")],
			[InlineKeyboardButton(text="❌ Отклонить лот", callback_data="lots:reject_from_doc")],
			[InlineKeyboardButton(text="🔙 Назад к лотам", callback_data="lots:back")]
		])
		
		await send_long_message(
			query.message.bot,
			query.message.chat.id,
			f"📄 <b>Предварительный анализ документации</b>\n\n"
			f"📎 Файл: {filename}\n\n"
			f"{analysis}",
			parse_mode="HTML",
			reply_markup=keyboard
		)
		
		# НЕ очищаем state, т.к. данные нужны для поиска поставщиков
		# query.answer уже был вызван в начале функции
		
	except Exception as e:
		logger.error(f"Error analyzing manual documentation: {e}", exc_info=True)
		error_msg = str(e)
		# Более понятное сообщение для типичных ошибок
		if "query is too old" in error_msg.lower() or "timeout" in error_msg.lower():
			user_message = (
				"❌ <b>Ошибка при анализе документации</b>\n\n"
				"Callback query устарел. Это может произойти, если анализ занял слишком много времени.\n\n"
				"<b>Попробуйте:</b>\n"
				"1. Начать анализ заново\n"
				"2. Использовать файл меньшего размера\n"
				"3. Проверить подключение к интернету"
			)
		else:
			user_message = (
				f"❌ <b>Ошибка при анализе документации</b>\n\n"
				f"<code>{error_msg}</code>\n\n"
				f"Попробуйте еще раз или обратитесь к администратору."
			)
		
		try:
			await query.message.edit_text(user_message, parse_mode="HTML")
		except Exception:
			await query.message.answer(user_message, parse_mode="HTML")


@router.callback_query(F.data == "lots:search_supplier_from_doc")
async def search_supplier_from_documentation(query, db_user: User, state: FSMContext):
	"""Запуск поиска поставщиков из анализа документации"""
	# Сразу отвечаем на callback query, чтобы избежать ошибки "query is too old"
	try:
		await query.answer()
	except Exception:
		# Если query уже устарел, игнорируем ошибку
		pass
	
	data = await state.get_data()
	documentation_text = data.get("documentation_text", "")
	analysis = data.get("analysis", "")
	filename = data.get("filename", "документ")
	
	# Извлекаем информацию о товарах из анализа или документации
	# Пробуем найти названия товаров в анализе
	product_name = "товары из документации"
	
	# Если есть анализ, пытаемся извлечь название товара
	if analysis:
		# Ищем первое упоминание товара в анализе
		import re
		# Ищем паттерны типа "Название товара:" или "• Название товара:"
		match = re.search(r'(?:•|[-*])\s*([А-Яа-яA-Za-z0-9\s]+?)(?::|$)', analysis[:500])
		if match:
			product_name = match.group(1).strip()
	
	# Переходим к поиску поставщиков
	from bot.states.forms import SupplierSearchStates
	from bot.keyboards.inline import get_supplier_search_menu
	
	await state.set_state(SupplierSearchStates.choosing_method)
	await state.update_data(
		from_documentation=True,
		documentation_text=documentation_text,
		product_name=product_name
	)
	
	# Пробуем отредактировать сообщение, если не получится - отправляем новое
	try:
		await query.message.edit_text(
			f"🔍 <b>Поиск Поставщиков</b>\n\n"
			f"📎 Источник: анализ документации ({filename})\n"
			f"📦 Товар: {product_name}\n\n"
			f"Выберите метод поиска:",
			reply_markup=get_supplier_search_menu(),
			parse_mode="HTML"
		)
	except Exception:
		# Если не удалось отредактировать (query устарел), отправляем новое сообщение
		await query.message.answer(
			f"🔍 <b>Поиск Поставщиков</b>\n\n"
			f"📎 Источник: анализ документации ({filename})\n"
			f"📦 Товар: {product_name}\n\n"
			f"Выберите метод поиска:",
			reply_markup=get_supplier_search_menu(),
			parse_mode="HTML"
		)


@router.callback_query(F.data.startswith("lots:search_supplier:"))
async def search_supplier_from_lot(query, db_user: User, state: FSMContext):
	"""Запуск поиска поставщиков для конкретного лота"""
	# Сразу отвечаем на callback query, чтобы избежать ошибки "query is too old"
	try:
		await query.answer()
	except Exception:
		# Если query уже устарел, игнорируем ошибку
		pass
	
	lot_number = query.data.split(":")[-1]
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	if not lot:
		try:
			await query.answer("❌ Лот не найден", show_alert=True)
		except Exception:
			pass
		return
	
	# Используем название лота или номенклатуру для поиска
	product_name = lot.title
	if lot.nomenclature:
		product_name = ", ".join(lot.nomenclature[:3])  # Первые 3 позиции номенклатуры
	
	# Переходим к поиску поставщиков
	from bot.states.forms import SupplierSearchStates
	from bot.keyboards.inline import get_supplier_search_menu
	
	await state.set_state(SupplierSearchStates.choosing_method)
	await state.update_data(
		from_lot=True,
		lot_number=lot_number,
		product_name=product_name
	)
	
	# Пробуем отредактировать сообщение, если не получится - отправляем новое
	try:
		await query.message.edit_text(
			f"🔍 <b>Поиск Поставщиков</b>\n\n"
			f"📋 Лот: {lot_number}\n"
			f"📦 Товар: {product_name}\n\n"
			f"Выберите метод поиска:",
			reply_markup=get_supplier_search_menu(),
			parse_mode="HTML"
		)
	except Exception:
		# Если не удалось отредактировать (query устарел), отправляем новое сообщение
		await query.message.answer(
			f"🔍 <b>Поиск Поставщиков</b>\n\n"
			f"📋 Лот: {lot_number}\n"
			f"📦 Товар: {product_name}\n\n"
			f"Выберите метод поиска:",
			reply_markup=get_supplier_search_menu(),
			parse_mode="HTML"
		)


@router.callback_query(F.data == "lots:reject_from_doc")
async def reject_lot_from_documentation(query, db_user: User, state: FSMContext):
	"""Отклонение лота из анализа документации - возврат к списку лотов"""
	# Сразу отвечаем на callback query
	try:
		await query.answer("Лот отклонён")
	except Exception:
		pass
	
	await state.clear()
	
	# Пробуем отредактировать сообщение, если не получится - отправляем новое
	try:
		await query.message.edit_text("❌ Лот отклонён")
	except Exception:
		await query.message.answer("❌ Лот отклонён")
	
	# Возвращаемся к списку лотов
	await show_my_lots(query.message, db_user)


@router.callback_query(F.data.startswith("lots:reject:"))
async def reject_lot(query, db_user: User):
	"""Отклонение конкретного лота"""
	# Сразу отвечаем на callback query
	try:
		await query.answer("Лот отклонён")
	except Exception:
		pass
	
	lot_number = query.data.split(":")[-1]
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	if lot:
		# Устанавливаем статус просмотра как "rejected"
		lot.review_status = "rejected"
		await lot_repo.update(lot)
	
	# Пробуем отредактировать сообщение, если не получится - отправляем новое
	try:
		await query.message.edit_text(f"❌ Лот {lot_number} отклонён")
	except Exception:
		await query.message.answer(f"❌ Лот {lot_number} отклонён")
	
	# Возвращаемся к списку лотов
	await show_my_lots(query.message, db_user)


@router.callback_query(F.data.startswith("lots:set_in_work:"))
async def set_lot_in_work(query, db_user: User):
	"""Установка статуса 'В работу' для лота"""
	# Сразу отвечаем на callback query
	try:
		await query.answer("Лот взят в работу")
	except Exception:
		pass
	
	lot_number = query.data.split(":")[-1]
	
	async with async_session_maker() as session:
		lot_repo = LotRepository(session)
		lot = await lot_repo.get_by_lot_number(lot_number)
	
	if lot:
		# Устанавливаем статус просмотра как "in_work"
		lot.review_status = "in_work"
		await lot_repo.update(lot)
	
	# Пробуем отредактировать сообщение, если не получится - отправляем новое
	try:
		await query.message.edit_text(f"✅ Лот {lot_number} взят в работу")
	except Exception:
		await query.message.answer(f"✅ Лот {lot_number} взят в работу")
	
	# Возвращаемся к списку лотов
	await show_my_lots(query.message, db_user)

