"""Обработчики для формирования запросов коммерческого предложения (RFQ)"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.forms import RFQStates
from bot.keyboards.inline import get_rfq_actions_menu, get_rfq_confirm_menu
from services.rfq.generator import (
    generate_rfq_text,
    generate_rfq_text_from_document,
    parse_supplier_info_from_report,
    extract_emails_from_text
)
from services.notifications.email import send_email
from services.email.manager_email import ManagerEmailService
from services.email.templates import get_kp_request_template
from utils.encryption import decrypt_password
from database.repositories.user_repository import UserRepository
from database.repositories.user_pref_repository import UserPreferenceRepository
from database.connection import async_session_maker
from database.models import User
from config.settings import settings

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "rfq:finish")
async def finish_search(callback: CallbackQuery, state: FSMContext):
    """Завершение поиска поставщиков"""
    await state.clear()
    await callback.message.edit_text(
        "✅ Поиск поставщиков завершен.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "rfq:create")
async def create_rfq(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Создание запроса коммерческого предложения"""
    data = await state.get_data()
    product_name = data.get("product_name")
    products = data.get("products")  # Список товаров из документа
    search_result = data.get("search_result", "")
    suppliers_by_email = data.get("suppliers_by_email", {})  # Группировка поставщиков по email
    
    # Если есть список товаров из документа, используем его, иначе используем product_name
    if not products and not product_name:
        await callback.answer("❌ Не найдены данные о товаре. Начните поиск заново.", show_alert=True)
        return
    
    # Определяем, был ли поиск через документ
    # Проверяем флаг is_from_document из state (устанавливается при обработке документа)
    is_from_document = data.get("is_from_document", False)
    
    # Если флаг не установлен, определяем по наличию данных
    # Поиск через документ: есть products и suppliers_by_email
    if not is_from_document:
        is_from_document = bool(products and suppliers_by_email)
    
    # Если products не указан, создаем список из product_name для обратной совместимости
    if not products:
        products = [{"name": product_name, "quantity": None, "unit": None, "code": None}]
    
    # Получаем информацию менеджера из БД
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(db_user.telegram_id)
        
        manager_name = user.full_name if user else None
        manager_email = user.contact_email if user else None
        manager_phone = None  # TODO: добавить поле phone в User
        manager_position = "Менеджер по закупкам"  # TODO: добавить поле position в User
    
    # Генерируем текст запроса в зависимости от источника
    if is_from_document:
        # Для поиска через документ используем упрощенную форму (без кода номенклатуры и технических требований)
        rfq_text = generate_rfq_text_from_document(
            products=products,
            manager_name=manager_name,
            manager_position=manager_position,
            manager_phone=manager_phone,
            manager_email=manager_email or settings.COMPANY_EMAIL,
            company_inn=None  # TODO: добавить ИНН компании в settings
        )
    else:
        # Для ручного ввода используем полную форму с техническими требованиями
        rfq_text = generate_rfq_text(
            products=products,
            manager_name=manager_name,
            manager_position=manager_position,
            manager_phone=manager_phone,
            manager_email=manager_email or settings.COMPANY_EMAIL,
            company_inn=None  # TODO: добавить ИНН компании в settings
        )
    
    # Парсим email адреса из отчета поиска
    # Показываем пользователю, что идет дополнительный поиск email
    await callback.message.edit_text(
        "⏳ <b>Формирование запроса...</b>\n\n"
        "🔍 Поиск email адресов поставщиков:\n"
        "• Парсинг отчета поиска\n"
        "• Поиск на веб-сайтах поставщиков\n\n"
        "Пожалуйста, подождите...",
        parse_mode="HTML"
    )
    
    # Если есть группировка поставщиков по email из поиска по документу, используем её
    emails = []
    if suppliers_by_email:
        # Извлекаем уникальные email адреса из группировки
        emails = list(suppliers_by_email.keys())
        supplier_info = {
            'emails': emails,
            'companies': [
                {
                    'name': info['supplier'].get('name', ''),
                    'email': email,
                    'phone': info['supplier'].get('phone'),
                    'website': info['supplier'].get('website'),
                    'products': info['products']  # Список товаров для этого поставщика
                }
                for email, info in suppliers_by_email.items()
            ]
        }
    else:
        # Парсим email адреса из отчета поиска и веб-сайтов (для обратной совместимости)
        # Ограничиваем до 20 компаний с email
        supplier_info = await parse_supplier_info_from_report(
            search_result,
            parse_websites=True,
            max_companies=20
        )
        emails = supplier_info.get('emails', [])
    
    # Удаляем дубликаты email адресов (приводим к нижнему регистру для сравнения)
    emails_lower = [e.lower() for e in emails]
    unique_emails = []
    seen = set()
    for email in emails:
        email_lower = email.lower()
        if email_lower not in seen:
            seen.add(email_lower)
            unique_emails.append(email)
    emails = unique_emails
    
    # Определяем название товара для отображения (используем первый товар или product_name)
    display_product_name = products[0].get("name") if products else product_name
    
    # Сохраняем данные в state
    await state.update_data(
        rfq_text=rfq_text,
        product_name=display_product_name,
        products=products,  # Сохраняем список всех товаров
        supplier_emails=emails,
        supplier_info=supplier_info,
        suppliers_by_email=suppliers_by_email,
        is_from_document=is_from_document  # Флаг для определения типа формы
    )
    await state.set_state(RFQStates.viewing_rfq_draft)
    
    # Формируем сообщение для отправки
    products_count = len(products) if products else 1
    preview_text = (
        f"📝 <b>Запрос коммерческого предложения</b>\n\n"
        f"<b>Количество товаров:</b> {products_count}\n"
    )
    
    if products_count == 1:
        preview_text += f"<b>Товар:</b> {display_product_name}\n\n"
    else:
        preview_text += f"<b>Товары:</b>\n"
        for idx, p in enumerate(products[:5], 1):  # Показываем первые 5
            preview_text += f"{idx}. {p.get('name', '')[:50]}"
            quantity = p.get('quantity')
            unit = p.get('unit')
            if quantity and unit:
                preview_text += f" (кол-во: {quantity} {unit})"
            elif quantity:
                preview_text += f" (кол-во: {quantity})"
            elif unit:
                preview_text += f" (ед. изм.: {unit})"
            preview_text += "\n"
        if len(products) > 5:
            preview_text += f"... и еще {len(products) - 5} товаров\n"
        preview_text += "\n"
    
    preview_text += f"<b>Найдено уникальных email адресов:</b> {len(emails)}\n"
    
    if emails:
        preview_text += f"<i>Адреса: {', '.join(emails[:3])}"
        if len(emails) > 3:
            preview_text += f" и еще {len(emails) - 3}..."
        preview_text += "</i>\n\n"
    
    preview_text += f"<b>Текст запроса:</b>\n\n{rfq_text[:500]}..."
    
    await callback.message.edit_text(
        preview_text,
        parse_mode="HTML",
        reply_markup=get_rfq_actions_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "rfq:edit")
async def edit_rfq(callback: CallbackQuery, state: FSMContext):
    """Редактирование текста запроса"""
    data = await state.get_data()
    rfq_text = data.get("rfq_text", "")
    
    if not rfq_text:
        await callback.answer("❌ Не найден текст запроса.", show_alert=True)
        return
    
    await state.set_state(RFQStates.editing_rfq_text)
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование запроса</b>\n\n"
        f"Отправьте исправленный текст запроса:\n\n"
        f"<code>{rfq_text}</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(RFQStates.editing_rfq_text)
async def process_rfq_edit(message: Message, state: FSMContext):
    """Обработка отредактированного текста запроса"""
    new_text = message.text.strip()
    
    if not new_text:
        await message.answer("❌ Текст не может быть пустым.")
        return
    
    # Сохраняем обновленный текст
    await state.update_data(rfq_text=new_text)
    await state.set_state(RFQStates.viewing_rfq_draft)
    
    data = await state.get_data()
    product_name = data.get("product_name", "")
    products = data.get("products")
    emails = data.get("supplier_emails", [])
    
    # Определяем название товара для отображения
    if products and len(products) > 0:
        if len(products) == 1:
            display_product_name = products[0].get("name", product_name)
            products_info = f"<b>Товар:</b> {display_product_name}\n\n"
        else:
            products_info = f"<b>Товаров:</b> {len(products)}\n\n"
    else:
        products_info = f"<b>Товар:</b> {product_name}\n\n"
    
    preview_text = (
        f"✅ <b>Запрос обновлен</b>\n\n"
        f"{products_info}"
        f"<b>Найдено email адресов:</b> {len(emails)}\n\n"
        f"<b>Текст запроса:</b>\n\n{new_text[:500]}..."
    )
    
    await message.answer(
        preview_text,
        parse_mode="HTML",
        reply_markup=get_rfq_actions_menu()
    )


@router.callback_query(F.data == "rfq:send")
async def prepare_send_rfq(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Подготовка к отправке запроса"""
    data = await state.get_data()
    rfq_text = data.get("rfq_text", "")
    emails = data.get("supplier_emails", [])
    product_name = data.get("product_name", "")
    products = data.get("products")
    
    # Определяем название товара для отображения
    if products and len(products) > 0:
        if len(products) == 1:
            display_product_name = products[0].get("name", product_name)
        else:
            display_product_name = f"{len(products)} товаров"
    else:
        display_product_name = product_name
    
    logger.info(f"prepare_send_rfq called: rfq_text={bool(rfq_text)}, emails={len(emails) if emails else 0}, products={len(products) if products else 0}, product_name={display_product_name}")
    
    if not rfq_text:
        logger.warning("rfq:send - rfq_text is empty")
        await callback.answer("❌ Не найден текст запроса.", show_alert=True)
        return
    
    # Разрешаем отправку даже если emails пустой - используем тестовый адрес
    if not emails:
        logger.warning(f"rfq:send - emails is empty, will use test recipient")
        emails = []  # Будем использовать тестовый адрес
    
    # Получаем настройки менеджера
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        pref_repo = UserPreferenceRepository(session)
        user = await user_repo.get_by_telegram_id(db_user.telegram_id)
        pref = await pref_repo.get_or_create(db_user.id)
    
    manager_email = user.contact_email if user else None
    has_email_config = (
        manager_email and
        pref.email_password and
        pref.smtp_provider
    )
    
    # ТЕСТОВЫЙ РЕЖИМ: всегда используем тестовый адрес
    # В production заменить на: recipients = emails if emails else [test_recipient]
    test_recipient = "nedyakin17@gmail.com"  # Тестовый получатель
    
    # Удаляем дубликаты email адресов перед отправкой
    emails_lower = [e.lower() for e in emails]
    unique_emails = []
    seen = set()
    for email in emails:
        email_lower = email.lower()
        if email_lower not in seen:
            seen.add(email_lower)
            unique_emails.append(email)
    
    recipients = [test_recipient]  # На этапе тестирования всегда отправляем на тестовый адрес
    
    # Логируем информацию о найденных email для отладки
    if unique_emails:
        logger.info(f"rfq:send - found {len(unique_emails)} unique supplier emails (from {len(emails)} total), but using test recipient in test mode")
    else:
        logger.info(f"rfq:send - no supplier emails found, using test recipient")
    
    sender_info = ""
    if has_email_config:
        sender_info = f"<b>Отправитель:</b> {manager_email} ({pref.smtp_provider})\n"
    else:
        sender_info = f"<b>Отправитель:</b> sened17@yandex.ru (тестовый режим)\n"
        sender_info += "<i>⚠️ Email менеджера не настроен. Настройте в разделе 'Настройки' → 'Настройка Email'</i>\n"
    
    # Добавляем информацию о тестовом режиме
    sender_info += f"\n<i>🧪 <b>ТЕСТОВЫЙ РЕЖИМ:</b> отправка на тестовый адрес nedyakin17@gmail.com</i>\n"
    
    await state.set_state(RFQStates.confirming_send)
    
    try:
        products_info = ""
        if products and len(products) > 1:
            products_info = f"<b>Товары ({len(products)}):</b>\n"
            for idx, p in enumerate(products[:3], 1):
                products_info += f"{idx}. {p.get('name', '')[:40]}"
                quantity = p.get('quantity')
                unit = p.get('unit')
                if quantity and unit:
                    products_info += f" (кол-во: {quantity} {unit})"
                elif quantity:
                    products_info += f" (кол-во: {quantity})"
                elif unit:
                    products_info += f" (ед. изм.: {unit})"
                products_info += "\n"
            if len(products) > 3:
                products_info += f"... и еще {len(products) - 3} товаров\n"
            products_info += "\n"
        else:
            products_info = f"<b>Товар:</b> {display_product_name}\n\n"
        
        await callback.message.edit_text(
            f"📧 <b>Подтверждение отправки</b>\n\n"
            f"{products_info}"
            f"{sender_info}\n"
            f"<b>Получатели:</b> {len(recipients)} адресов\n"
            f"<i>{', '.join(recipients[:3])}"
            + (f" и еще {len(recipients) - 3}..." if len(recipients) > 3 else "") + "</i>\n\n"
            f"<b>Текст запроса:</b>\n\n"
            f"<code>{rfq_text[:300]}...</code>\n\n"
            f"Продолжить отправку?",
            parse_mode="HTML",
            reply_markup=get_rfq_confirm_menu()
        )
        await callback.answer()
        logger.info(f"rfq:send - confirmation message sent successfully")
    except Exception as e:
        logger.error(f"rfq:send - error editing message: {e}", exc_info=True)
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "rfq:confirm_send")
async def confirm_send_rfq(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Подтверждение и отправка запроса"""
    data = await state.get_data()
    rfq_text = data.get("rfq_text", "")
    emails = data.get("supplier_emails", [])
    product_name = data.get("product_name", "")
    
    if not rfq_text:
        await callback.answer("❌ Не найден текст запроса.", show_alert=True)
        return
    
    # Получаем настройки менеджера
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        pref_repo = UserPreferenceRepository(session)
        user = await user_repo.get_by_telegram_id(db_user.telegram_id)
        pref = await pref_repo.get_or_create(db_user.id)
    
    # Проверяем, настроен ли email менеджера
    manager_email = user.contact_email if user else None
    has_email_config = (
        manager_email and
        pref.email_password and
        pref.smtp_provider
    )
    
    # ТЕСТОВЫЙ РЕЖИМ: всегда используем тестовый адрес
    # В production заменить на: recipients = emails if emails else [test_recipient]
    test_recipient = "nedyakin17@gmail.com"  # Тестовый получатель
    
    # Удаляем дубликаты email адресов перед отправкой
    emails_lower = [e.lower() for e in emails]
    unique_emails = []
    seen = set()
    for email in emails:
        email_lower = email.lower()
        if email_lower not in seen:
            seen.add(email_lower)
            unique_emails.append(email)
    
    recipients = [test_recipient]  # На этапе тестирования всегда отправляем на тестовый адрес
    
    # Логируем информацию о найденных email для отладки
    if unique_emails:
        logger.info(f"rfq:confirm_send - found {len(unique_emails)} unique supplier emails (from {len(emails)} total), but using test recipient in test mode")
    else:
        logger.info(f"rfq:confirm_send - no supplier emails found, using test recipient: {test_recipient}")
    
    # Определяем название товара для темы письма
    products = data.get("products")
    if products and len(products) > 0:
        if len(products) == 1:
            display_product_name = products[0].get("name", product_name)
        else:
            display_product_name = f"{len(products)} товаров"
    else:
        display_product_name = product_name
    
    # Формируем тему письма
    subject = f"Запрос коммерческого предложения: {display_product_name}"
    
    # Формируем данные компании для шаблона
    company_data = {
        'manager_name': user.full_name if user else "Менеджер",
        'manager_position': "Менеджер по закупкам",
        'phone': None,  # TODO: добавить поле phone в User
        'email': manager_email or settings.COMPANY_EMAIL
    }
    
    # Извлекаем технические требования из rfq_text
    is_from_document = data.get("is_from_document", False)
    specifications = ""
    
    if is_from_document:
        # Для документа извлекаем только часть до "Требуемая информация", чтобы избежать дублирования
        if "Требуемая информация:" in rfq_text:
            specifications = rfq_text.split("Требуемая информация:")[0].strip()
        else:
            # Если раздела нет, берем весь текст до конца
            specifications = rfq_text
    elif "Технические требования:" in rfq_text:
        # Для обычной формы извлекаем раздел "Технические требования"
        parts = rfq_text.split("Технические требования:")
        if len(parts) > 1:
            specs_part = parts[1].split("Требуемая информация:")[0].strip()
            specifications = specs_part
    
    # Формируем текст для шаблона с учетом всех товаров
    if products and len(products) > 1:
        products_text = "\n".join([
            f"{idx}. {p.get('name', '')}" + (
                f" (кол-во: {p.get('quantity')} {p.get('unit')})" if p.get('quantity') and p.get('unit') else
                f" (кол-во: {p.get('quantity')})" if p.get('quantity') else
                f" (ед. изм.: {p.get('unit')})" if p.get('unit') else ""
            )
            for idx, p in enumerate(products, 1)
        ])
        product_name_for_template = f"{len(products)} товаров:\n{products_text}"
    else:
        product_name_for_template = display_product_name
    
    # Используем шаблон письма
    # Если specifications пустой, используем часть rfq_text (но не более 500 символов)
    body_html = get_kp_request_template(
        product_name=product_name_for_template,
        specifications=specifications if specifications else rfq_text[:500],
        company_data=company_data
    )
    
    try:
        # Если email менеджера настроен, используем его настройки
        if has_email_config:
            logger.info(f"rfq:confirm_send - using manager email config: {manager_email} ({pref.smtp_provider})")
            email_service = ManagerEmailService(
                email=manager_email,
                password=pref.email_password,
                smtp_provider=pref.smtp_provider
            )
            sent = await email_service.send_email(
                subject=subject,
                body_html=body_html,
                recipients=recipients
            )
        else:
            # Fallback: используем тестовую конфигурацию sened17@yandex.ru
            logger.warning(f"Manager email not configured for user {db_user.telegram_id}, using test config")
            # Для тестирования используем настройки из .env или тестовые
            test_email = "sened17@yandex.ru"
            # Пытаемся использовать глобальные настройки SMTP, если они есть
            if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASS:
                logger.info("Using global SMTP settings for test")
                sent = await send_email(
                    subject=subject,
                    body_html=body_html,
                    recipients=recipients
                )
            else:
                logger.error("No email configuration available - neither manager nor global SMTP")
                await callback.message.edit_text(
                    "❌ <b>Ошибка отправки</b>\n\n"
                    "Email не настроен. Настройте email в разделе 'Настройки' → 'Настройка Email'.\n\n"
                    "Для тестирования необходимо:\n"
                    "1. Указать email: sened17@yandex.ru\n"
                    "2. Указать пароль приложения Yandex\n"
                    "3. Выбрать провайдер: Yandex",
                    parse_mode="HTML"
                )
                await callback.answer("❌ Email не настроен", show_alert=True)
                return
        
        if sent:
            products_info = ""
            if products and len(products) > 1:
                products_info = f"<b>Товаров:</b> {len(products)}\n"
            else:
                products_info = f"<b>Товар:</b> {display_product_name}\n"
            
            await callback.message.edit_text(
                f"✅ <b>Запрос отправлен успешно!</b>\n\n"
                f"{products_info}"
                f"<b>Получателей:</b> {len(recipients)}\n"
                f"<b>Адреса:</b> {', '.join(recipients)}\n\n"
                f"🧪 <i>ТЕСТОВЫЙ РЕЖИМ: отправка на тестовый адрес nedyakin17@gmail.com</i>\n\n"
                f"Запрос коммерческого предложения был отправлен.",
                parse_mode="HTML"
            )
            logger.info(f"RFQ sent for {len(products) if products else 1} product(s) ({display_product_name}) to {recipients}")
        else:
            await callback.message.edit_text(
                f"❌ <b>Ошибка отправки запроса</b>\n\n"
                f"Не удалось отправить email. Проверьте настройки SMTP в .env файле.",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error sending RFQ: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ <b>Ошибка при отправке:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )
    
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == "rfq:cancel")
async def cancel_rfq(callback: CallbackQuery, state: FSMContext):
    """Отмена формирования запроса"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Формирование запроса отменено.",
        parse_mode="HTML"
    )
    await callback.answer()

