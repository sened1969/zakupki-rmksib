"""GUI handlers для настройки предпочтений"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.models import User
from database import async_session_maker, UserPreferenceRepository, UserRepository
from bot.keyboards.inline import get_preferences_menu, get_customer_selection, get_nomenclature_selection, get_notify_toggle, get_customer_fetch_menu

router = Router()


@router.callback_query(F.data == "pref:cust")
async def customers_menu(callback: CallbackQuery, db_user: User):
	"""Меню выбора заказчиков"""
	import logging
	logger = logging.getLogger(__name__)
	
	try:
		async with async_session_maker() as session:
			pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
		
		# Обрабатываем customers - может быть список или None
		customers_list = pref.customers
		if customers_list is not None and not isinstance(customers_list, list):
			# Если это не список, преобразуем
			logger.warning(f"customers is not a list: {type(customers_list)}, value: {customers_list}")
			customers_list = list(customers_list) if customers_list else None
		
		logger.info(f"Opening customers menu for user {db_user.id}, customers: {customers_list}")
		
		await callback.message.edit_text(
			"🏢 <b>Выберите заказчиков:</b>\n\nНажмите на название, чтобы выбрать/снять выбор.",
			parse_mode="HTML",
			reply_markup=get_customer_selection(customers_list)
		)
		await callback.answer()
	except Exception as e:
		logger.error(f"Error in customers_menu: {e}", exc_info=True)
		await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("cust_t:"))
async def toggle_customer(callback: CallbackQuery, db_user: User):
	"""Переключить выбор заказчика"""
	from config.customers import CUSTOMERS_LIST
	
	try:
		# Получаем индекс из callback_data
		idx = int(callback.data.split(":")[1])
		if idx < 0 or idx >= len(CUSTOMERS_LIST):
			await callback.answer("❌ Неверный индекс заказчика", show_alert=True)
			return
		
		customer = CUSTOMERS_LIST[idx]
		
		async with async_session_maker() as session:
			pref_repo = UserPreferenceRepository(session)
			pref = await pref_repo.get_or_create(db_user.id)
			current = set(pref.customers or [])
			if customer in current:
				current.remove(customer)
			else:
				current.add(customer)
			pref.customers = list(current)
			await pref_repo.update_lists(pref, customers=pref.customers)
		
		await callback.message.edit_reply_markup(reply_markup=get_customer_selection(pref.customers))
		await callback.answer()
	except (ValueError, IndexError) as e:
		import logging
		logger = logging.getLogger(__name__)
		logger.error(f"Error parsing customer index: {e}, callback_data: {callback.data}")
		await callback.answer("❌ Ошибка обработки", show_alert=True)


@router.callback_query(F.data == "cust_save")
async def save_customers(callback: CallbackQuery, db_user: User):
	"""Сохранить выбранных заказчиков"""
	async with async_session_maker() as session:
		pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
	msg = f"✅ Заказчики сохранены: {', '.join(pref.customers or []) or 'все'}"
	await callback.message.edit_text(msg, reply_markup=None)
	await callback.answer(msg)


@router.callback_query(F.data == "pref:nom")
async def nomenclature_menu(callback: CallbackQuery, db_user: User):
	"""Меню выбора номенклатуры"""
	import logging
	logger = logging.getLogger(__name__)
	
	try:
		async with async_session_maker() as session:
			pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
		
		# Обрабатываем nomenclature - может быть список или None
		nomenclature_list = pref.nomenclature
		if nomenclature_list is not None and not isinstance(nomenclature_list, list):
			# Если это не список, преобразуем
			logger.warning(f"nomenclature is not a list: {type(nomenclature_list)}, value: {nomenclature_list}")
			nomenclature_list = list(nomenclature_list) if nomenclature_list else None
		
		logger.info(f"Opening nomenclature menu for user {db_user.id}, nomenclature: {nomenclature_list}")
		
		await callback.message.edit_text(
			"🏷 <b>Выберите номенклатуру:</b>\n\nНажмите на название, чтобы выбрать/снять выбор.",
			parse_mode="HTML",
			reply_markup=get_nomenclature_selection(nomenclature_list)
		)
		await callback.answer()
	except Exception as e:
		logger.error(f"Error in nomenclature_menu: {e}", exc_info=True)
		await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("nom_t:"))
async def toggle_nomenclature(callback: CallbackQuery, db_user: User):
	"""Переключить выбор номенклатуры"""
	from config.nomenclature import NOMENCLATURE_LIST
	
	try:
		# Получаем индекс из callback_data
		idx = int(callback.data.split(":")[1])
		if idx < 0 or idx >= len(NOMENCLATURE_LIST):
			await callback.answer("❌ Неверный индекс номенклатуры", show_alert=True)
			return
		
		nomenclature = NOMENCLATURE_LIST[idx]
		
		async with async_session_maker() as session:
			pref_repo = UserPreferenceRepository(session)
			pref = await pref_repo.get_or_create(db_user.id)
			current = set(pref.nomenclature or [])
			if nomenclature in current:
				current.remove(nomenclature)
			else:
				current.add(nomenclature)
			pref.nomenclature = list(current)
			await pref_repo.update_lists(pref, nomenclature=pref.nomenclature)
		
		await callback.message.edit_reply_markup(reply_markup=get_nomenclature_selection(pref.nomenclature))
		await callback.answer()
	except (ValueError, IndexError) as e:
		import logging
		logger = logging.getLogger(__name__)
		logger.error(f"Error parsing nomenclature index: {e}, callback_data: {callback.data}")
		await callback.answer("❌ Ошибка обработки", show_alert=True)


@router.callback_query(F.data == "nom_save")  # ✅ Правильно!
async def save_nomenclature(callback: CallbackQuery, db_user: User):
	"""Сохранить выбранную номенклатуру"""
	async with async_session_maker() as session:
		pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
	msg = f"✅ Номенклатура сохранена: {', '.join(pref.nomenclature or []) or 'вся'}"
	await callback.message.edit_text(msg, reply_markup=None)
	await callback.answer(msg)


@router.callback_query(F.data == "pref:notify")
async def notify_menu(callback: CallbackQuery, db_user: User):
	"""Меню переключения уведомлений"""
	async with async_session_maker() as session:
		pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
	status = "✅ Включены" if pref.notify_enabled else "❌ Выключены"
	await callback.message.edit_text(
		f"🔔 <b>Уведомления:</b> {status}\n\nНажмите кнопку ниже, чтобы изменить.",
		parse_mode="HTML",
		reply_markup=get_notify_toggle(pref.notify_enabled)
	)
	await callback.answer()


@router.callback_query(F.data.startswith("notify_toggle:"))
async def toggle_notify(callback: CallbackQuery, db_user: User):
	"""Переключить уведомления"""
	enabled_str = callback.data.split(":", 1)[1]
	enabled = enabled_str.lower() == "true"
	async with async_session_maker() as session:
		pref_repo = UserPreferenceRepository(session)
		pref = await pref_repo.get_or_create(db_user.id)
		await pref_repo.set_notify(pref, enabled)
	msg = "🔔 Уведомления включены" if enabled else "🔕 Уведомления выключены"
	await callback.message.edit_text(msg, reply_markup=None)
	await callback.answer(msg)


@router.callback_query(F.data == "pref:back")
async def back_to_main(callback: CallbackQuery, db_user: User):
	"""Вернуться в главное меню"""
	async with async_session_maker() as session:
		pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
		user_repo = UserRepository(session)
		user = await user_repo.get_by_telegram_id(db_user.telegram_id)
	
	text = "⚙️ <b>Ваши настройки</b>\n\n"
	text += "👤 <b>Профиль:</b>\n"
	text += f"  Имя: {user.full_name if user else db_user.full_name or 'Не указано'}\n"
	text += f"  Email: {user.contact_email if user else db_user.contact_email or 'Не указан'}\n"
	text += f"  Роль: {'👑 Администратор' if db_user.role == 'admin' else '👤 Менеджер' if db_user.role == 'manager' else '👤 Пользователь'}\n\n"
	text += "🔔 <b>Уведомления:</b>\n"
	text += f"  Статус: {'✅ Включены' if pref.notify_enabled else '❌ Выключены'}\n"
	text += f"  Заказчики: {', '.join(pref.customers or []) or 'все'}\n"
	text += f"  Номенклатура: {', '.join(pref.nomenclature or []) or 'вся'}\n"
	text += f"  Бюджет: {f'{pref.budget_min:,} - {pref.budget_max:,} ₽' if pref.budget_min and pref.budget_max else 'не установлен'}\n\n"
	text += "📧 <b>Email для рассылки КП:</b>\n"
	text += f"  Провайдер: {pref.smtp_provider or 'не выбран'}\n"
	text += f"  Пароль: {'✅ установлен' if pref.email_password else '❌ не установлен'}\n\n"
	text += "Используйте кнопки ниже для настройки."
	
	await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_preferences_menu())
	await callback.answer()


@router.callback_query(F.data == "pref:close")
async def close_menu(callback: CallbackQuery):
	"""Закрыть меню"""
	await callback.message.delete()
	await callback.answer("❌ Меню закрыто")


@router.callback_query(F.data == "pref:fetch_lots")
async def show_customer_fetch_menu(callback: CallbackQuery, db_user: User):
	"""Показать меню запроса закупок по заказчикам"""
	text = (
		"🔄 <b>Запрос актуальных закупок</b>\n\n"
		"Выберите заказчика для запроса актуальных закупок:\n\n"
		"✅ - парсер настроен и активен\n"
		"⚠️ - требуется настройка B2B-Center API"
	)
	
	await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_customer_fetch_menu())
	await callback.answer()


@router.callback_query(F.data == "pref:menu")
async def open_preferences_menu(callback: CallbackQuery, db_user: User):
	"""Открыть меню настроек из других разделов"""
	async with async_session_maker() as session:
		pref = await UserPreferenceRepository(session).get_or_create(db_user.id)
		user_repo = UserRepository(session)
		user = await user_repo.get_by_telegram_id(db_user.telegram_id)
	
	text = "⚙️ <b>Ваши настройки</b>\n\n"
	text += "👤 <b>Профиль:</b>\n"
	text += f"  Имя: {user.full_name if user else db_user.full_name or 'Не указано'}\n"
	text += f"  Email: {user.contact_email if user else db_user.contact_email or 'Не указан'}\n"
	text += f"  Роль: {'👑 Администратор' if db_user.role == 'admin' else '👤 Менеджер' if db_user.role == 'manager' else '👤 Пользователь'}\n\n"
	text += "🔔 <b>Уведомления:</b>\n"
	text += f"  Статус: {'✅ Включены' if pref.notify_enabled else '❌ Выключены'}\n"
	text += f"  Заказчики: {', '.join(pref.customers or []) or 'все'}\n"
	text += f"  Номенклатура: {', '.join(pref.nomenclature or []) or 'вся'}\n"
	text += f"  Бюджет: {f'{pref.budget_min:,} - {pref.budget_max:,} ₽' if pref.budget_min and pref.budget_max else 'не установлен'}\n\n"
	text += "📧 <b>Email для рассылки КП:</b>\n"
	text += f"  Провайдер: {pref.smtp_provider or 'не выбран'}\n"
	text += f"  Пароль: {'✅ установлен' if pref.email_password else '❌ не установлен'}\n\n"
	text += "Используйте кнопки ниже для настройки."
	
	await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_preferences_menu())
	await callback.answer()


@router.callback_query(F.data.startswith("fetch_cust:"))
async def fetch_customer_lots(callback: CallbackQuery, db_user: User):
	"""Запрос закупок для конкретного заказчика"""
	from config.customers import CUSTOMERS_LIST
	from services.parsers import run_parser_for_customer
	
	# Получаем индекс заказчика из callback_data
	try:
		customer_idx = int(callback.data.split(":")[1])
		if customer_idx < 0 or customer_idx >= len(CUSTOMERS_LIST):
			await callback.answer("❌ Неверный индекс заказчика", show_alert=True)
			return
		
		customer_name = CUSTOMERS_LIST[customer_idx]
	except (ValueError, IndexError):
		await callback.answer("❌ Ошибка при обработке запроса", show_alert=True)
		return
	
	# Показываем сообщение о начале запроса
	await callback.message.edit_text(f"🔄 Запрашиваю актуальные закупки для <b>{customer_name}</b>...", parse_mode="HTML")
	await callback.answer()
	
	# Запускаем парсер
	try:
		new_count, message = await run_parser_for_customer(customer_name)
		
		# Отправляем результат
		await callback.message.edit_text(message, parse_mode="HTML", reply_markup=get_customer_fetch_menu())
		
	except Exception as e:
		import logging
		logger = logging.getLogger(__name__)
		logger.error(f"Error fetching lots for {customer_name}: {e}", exc_info=True)
		await callback.message.edit_text(
			f"❌ <b>Ошибка при запросе закупок</b>\n\n"
			f"Заказчик: {customer_name}\n"
			f"Ошибка: {str(e)}\n\n"
			f"Попробуйте еще раз или обратитесь к администратору.",
			parse_mode="HTML",
			reply_markup=get_customer_fetch_menu()
		)
