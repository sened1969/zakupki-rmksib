"""Обработчики для работы с коммерческими предложениями"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Document
from bot.states.forms import CommercialProposalStates
from database.models import User, CommercialProposal
from database import async_session_maker, LotRepository
from database.repositories.commercial_proposal_repository import CommercialProposalRepository
from services.documentation import save_documentation_file, extract_text_from_file, is_supported_format
from services.ai.commercial_proposal_analysis import analyze_supplier_reliability, calculate_integral_rating
from services.cp_data_extraction import extract_cp_data_combined
from utils.formatters import format_rub, format_separator
from bot.keyboards.inline import get_main_menu_button
from pathlib import Path
from datetime import datetime
import logging
import re

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "📄 Анализ КП")
async def show_cp_menu(message: Message, db_user: User, state: FSMContext) -> None:
    """Начать процесс загрузки КП - сразу запрашиваем файл"""
    logger.info(f"CP menu button pressed by user {db_user.id}")
    try:
        # Проверяем наличие таблицы через попытку получить список КП
        async with async_session_maker() as session:
            cp_repo = CommercialProposalRepository(session)
            proposals = await cp_repo.get_all(user_id=db_user.id, limit=100)
        
        # Если есть загруженные КП, показываем их количество и предлагаем загрузить еще или сформировать отчет
        if proposals:
            text = f"📄 <b>Анализ коммерческих предложений</b>\n\n"
            text += f"Загружено КП: {len(proposals)}\n\n"
            text += "📎 <b>Загрузите файл коммерческого предложения</b> (PDF, DOCX, DOC, TXT, RTF, Excel):"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Сформировать отчет сравнения", callback_data="cp:compare")],
                [InlineKeyboardButton(text="🗑️ Очистить все КП", callback_data="cp:clear_all")],
                [InlineKeyboardButton(text="🔄 Загрузить новые КП", callback_data="cp:start_new")],
                get_main_menu_button()
            ])
            
            await state.set_state(CommercialProposalStates.uploading_proposal)
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            # Если КП нет, просто запрашиваем загрузку
            text = "📄 <b>Анализ коммерческих предложений</b>\n\n"
            text += "📎 <b>Загрузите файл коммерческого предложения</b> (PDF, DOCX, DOC, TXT, RTF, Excel):"
            
            await state.set_state(CommercialProposalStates.uploading_proposal)
            await message.answer(text, parse_mode="HTML")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error showing CP menu: {e}", exc_info=True)
        
        # Проверяем, не связана ли ошибка с отсутствием таблицы
        if "does not exist" in error_msg.lower() or "no such table" in error_msg.lower() or "relation" in error_msg.lower():
            await message.answer(
                "❌ <b>Ошибка: таблица коммерческих предложений не найдена</b>\n\n"
                "Необходимо применить миграцию БД:\n"
                "<code>alembic upgrade head</code>\n\n"
                "После применения миграции функционал будет доступен.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Ошибка при открытии меню анализа КП</b>\n\n"
                f"Ошибка: {error_msg}\n\n"
                f"Проверьте логи бота для подробностей.",
                parse_mode="HTML"
            )


@router.callback_query(F.data == "cp:upload_next")
async def start_upload_next_cp(query, db_user: User, state: FSMContext):
    """Начать загрузку следующего КП"""
    await query.answer()
    await state.set_state(CommercialProposalStates.uploading_proposal)
    
    await query.message.edit_text(
        "📎 <b>Загрузите файл коммерческого предложения</b>\n\n"
        "Поддерживаемые форматы: PDF, DOCX, DOC, TXT, RTF, Excel (XLSX, XLS)",
        parse_mode="HTML"
    )


@router.message(StateFilter(CommercialProposalStates.entering_delivery_cost))
async def process_delivery_cost(message: Message, state: FSMContext, db_user: User):
    """Обработка ввода транспортных расходов - после ввода сохраняем КП и предлагаем загрузить следующее"""
    # Проверяем, не является ли это кнопкой меню
    from utils.menu_helpers import handle_menu_button_in_fsm
    
    if await handle_menu_button_in_fsm(message, state, message.text):
        # Если это кнопка меню, состояние очищено, пусть обработает соответствующий обработчик
        return
    
    logger.info(f"Processing delivery cost for user {db_user.id}")
    delivery_text = message.text.strip()
    delivery_cost = None
    
    if delivery_text != '-':
        try:
            # Удаляем все символы кроме цифр и точки/запятой
            price_text = re.sub(r'[^\d.,]', '', delivery_text.replace(' ', ''))
            price_text = price_text.replace(',', '.')
            delivery_cost = float(price_text)
            
            if delivery_cost < 0:
                raise ValueError("Транспортные расходы не могут быть отрицательными")
        except ValueError as e:
            logger.warning(f"Invalid delivery cost format: {delivery_text}, error: {e}")
            await message.answer(
                f"❌ Неверный формат суммы. Введите число или '-' если транспортные расходы не требуются:\n"
                f"Ошибка: {str(e)}"
            )
            return
    
    # Сохраняем данные
    data = await state.get_data()
    logger.info(f"State data keys: {list(data.keys())}")
    
    if not data.get('proposal_file_path'):
        logger.error("No proposal_file_path in state data")
        await message.answer(
            "❌ Ошибка: данные о файле не найдены. Пожалуйста, загрузите файл заново."
        )
        await state.clear()
        return
    
    # Извлекаем информацию о поставщике и цене из текста КП с помощью улучшенного модуля
    proposal_text = data.get('proposal_text', '')
    file_path = data.get('proposal_file_path')
    supplier_name = None  # Не используем значение по умолчанию
    product_price = 0.0  # По умолчанию
    items_count = None
    
    # Используем улучшенное извлечение данных
    if proposal_text or file_path:
        try:
            logger.info(f"Extracting CP data from text (length: {len(proposal_text) if proposal_text else 0}) and file: {file_path}")
            extracted_data = await extract_cp_data_combined(
                proposal_text=proposal_text or '',
                file_path=file_path,
                use_llm_fallback=True  # Используем LLM для сложных случаев
            )
            
            if extracted_data.get('supplier_name'):
                supplier_name = extracted_data['supplier_name']
                logger.info(f"Extracted supplier name: {supplier_name}")
            else:
                logger.warning("Supplier name not found in document")
            
            if extracted_data.get('total_amount'):
                product_price = float(extracted_data['total_amount'])
                logger.info(f"Extracted total amount: {product_price}")
            else:
                logger.warning("Total amount not found in document")
            
            if extracted_data.get('items_count'):
                items_count = int(extracted_data['items_count'])
                logger.info(f"Extracted items count: {items_count}")
            else:
                logger.warning("Items count not found in document")
        except Exception as e:
            logger.error(f"Error extracting CP data: {e}", exc_info=True)
            # В случае ошибки используем значения по умолчанию
    
    # Если поставщик не найден, используем значение по умолчанию только для сохранения
    if not supplier_name:
        supplier_name = "Поставщик (не определен)"
    
    # Сохраняем КП в БД
    try:
        logger.info(f"Saving CP: supplier={supplier_name}, price={product_price}, delivery={delivery_cost}")
        async with async_session_maker() as session:
            cp_repo = CommercialProposalRepository(session)
            
            proposal = await cp_repo.create(
                supplier_name=supplier_name,
                supplier_inn=None,  # ИНН не запрашиваем
                proposal_file_path=data.get('proposal_file_path'),
                proposal_text=proposal_text,
                product_price=product_price,
                delivery_cost=delivery_cost,
                other_conditions=None,  # Прочие условия не запрашиваем
                items_count=items_count,  # Количество наименований товара
                created_by=db_user.id
            )
            
            logger.info(f"CP saved with ID: {proposal.id}")
            
            # Получаем количество загруженных КП
            proposals = await cp_repo.get_all(user_id=db_user.id, limit=100)
            logger.info(f"Total proposals for user: {len(proposals)}")
        
        delivery_text_display = format_rub(delivery_cost) if delivery_cost is not None else "не указаны"
        
        separator = format_separator(30)
        text = f"{separator}\n"
        text += "✅ <b>Коммерческое предложение сохранено!</b>\n"
        text += f"{separator}\n\n"
        text += f"📎 <b>Файл:</b> {data.get('filename', 'неизвестен')}\n"
        text += f"🏢 <b>Поставщик:</b> {supplier_name}\n"
        text += f"💰 <b>Сумма:</b> {format_rub(product_price)}\n"
        text += f"🚚 <b>Транспортные расходы:</b> {delivery_text_display}\n"
        if items_count:
            text += f"📦 <b>Количество наименований:</b> {items_count}\n"
        text += "\n"
        text += f"{separator}\n"
        text += f"Всего загружено КП: <code>{len(proposals)}</code>\n\n"
        text += "Выберите действие:"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Загрузить следующее КП", callback_data="cp:upload_next")],
            [InlineKeyboardButton(text="📊 Сформировать отчет сравнения", callback_data="cp:compare")]
        ])
        
        await state.clear()
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        logger.info(f"Successfully saved CP and showed menu to user {db_user.id}")
        
    except Exception as e:
        logger.error(f"Error saving commercial proposal: {e}", exc_info=True)
        await message.answer(
            f"❌ <b>Ошибка при сохранении коммерческого предложения</b>\n\n"
            f"Ошибка: {str(e)}\n\n"
            f"Попробуйте загрузить файл снова через кнопку '📄 Анализ КП'.",
            parse_mode="HTML"
        )
        await state.clear()


@router.message(StateFilter(CommercialProposalStates.uploading_proposal), ~F.document)
async def handle_text_in_upload_state(message: Message, state: FSMContext, db_user: User):
    """Обработка текстовых сообщений в состоянии загрузки файла"""
    # Проверяем, не является ли это кнопкой меню
    from utils.menu_helpers import handle_menu_button_in_fsm
    
    if await handle_menu_button_in_fsm(message, state, message.text):
        # Если это кнопка меню, состояние очищено, пусть обработает соответствующий обработчик
        return
    
    await message.answer(
        "❌ Пожалуйста, отправьте <b>файл</b> коммерческого предложения, а не текст.\n\n"
        "Поддерживаемые форматы: PDF, DOCX, DOC, TXT, RTF, Excel (XLSX, XLS)\n\n"
        "💡 <i>Используйте кнопки меню для выхода из режима загрузки</i>",
        parse_mode="HTML"
    )


@router.message(StateFilter(CommercialProposalStates.uploading_proposal), F.document)
async def process_proposal_file(message: Message, state: FSMContext, db_user: User):
    """Обработка загрузки файла КП - после загрузки сразу запрашиваем транспортные расходы"""
    document = message.document
    
    if not document:
        await message.answer("❌ Файл не найден. Пожалуйста, отправьте файл коммерческого предложения.")
        return
    
    file_ext = Path(document.file_name).suffix.lower() if document.file_name else ''
    
    if not is_supported_format(document.file_name or ''):
        await message.answer(
            f"❌ Неподдерживаемый формат файла: {file_ext}\n\n"
            "Поддерживаемые форматы: PDF, DOCX, DOC, TXT, RTF, Excel (XLSX, XLS)\n\n"
            "Попробуйте загрузить файл снова:"
        )
        return
    
    # Скачиваем файл
    try:
        # В aiogram 3.x правильный способ - использовать download() напрямую с объектом документа
        import io
        buffer = io.BytesIO()
        # В aiogram 3.x download() принимает объект документа напрямую
        await message.bot.download(document, destination=buffer)
        file_bytes = buffer.getvalue()
        buffer.close()
        
        if not file_bytes:
            raise ValueError("Получен пустой файл")
        
        # Сохраняем файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CP_{timestamp}{file_ext}"
        filename = re.sub(r'[^\w\-_\.]', '_', filename)  # Очищаем имя файла
        
        file_path = await save_documentation_file(file_bytes, filename, lot_number=None)
        
        # Извлекаем текст из файла
        proposal_text = await extract_text_from_file(file_path)
        if not proposal_text or proposal_text.startswith("[Ошибка"):
            proposal_text = None
        
        # Сохраняем данные в состояние
        await state.update_data(
            proposal_file_path=file_path,
            proposal_text=proposal_text,
            filename=document.file_name
        )
        
        # Сразу переходим к вводу транспортных расходов
        await state.set_state(CommercialProposalStates.entering_delivery_cost)
        
        text = "✅ <b>Файл загружен!</b>\n\n"
        text += f"📎 Файл: {document.file_name}\n"
        text += f"📊 Размер: {document.file_size / 1024:.1f} КБ\n\n"
        text += "💰 <b>Введите прогнозную сумму транспортных расходов</b> в рублях\n"
        text += "(или отправьте '-' если транспортные расходы не требуются):"
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error processing proposal file: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при обработке файла: {str(e)}")


@router.callback_query(F.data == "cp:compare")
async def compare_proposals(query, db_user: User):
    """Формирование отчета сравнения КП"""
    await query.answer("📊 Формирую отчет сравнения...")
    
    async with async_session_maker() as session:
        cp_repo = CommercialProposalRepository(session)
        proposals = await cp_repo.get_all(user_id=db_user.id, limit=100)
    
    if not proposals:
        await query.message.edit_text(
            "❌ <b>Нет коммерческих предложений для сравнения</b>\n\n"
            "Сначала загрузите хотя бы одно коммерческое предложение.",
            parse_mode="HTML"
        )
        return
    
    # Анализируем КП, которые еще не были проанализированы
    await query.message.edit_text(
        "⏳ <b>Анализирую коммерческие предложения...</b>\n\n"
        "Это может занять некоторое время.",
        parse_mode="HTML"
    )
    
    analyzed_count = 0
    for proposal in proposals:
        if proposal.supplier_rating is None:
            # Анализируем надежность поставщика
            try:
                analysis_result = await analyze_supplier_reliability(
                    proposal.supplier_name,
                    proposal.supplier_inn
                )
                
                # Рассчитываем интегральный рейтинг
                integral_rating = calculate_integral_rating(
                    proposal.product_price,
                    proposal.delivery_cost,
                    analysis_result["rating"],
                    proposal.other_conditions
                )
                
                # Обновляем КП
                proposal.supplier_rating = analysis_result["rating"]
                proposal.supplier_reliability_info = analysis_result["reliability_info"]
                proposal.integral_rating = integral_rating
                proposal.analyzed_at = datetime.utcnow()
                
                async with async_session_maker() as session:
                    cp_repo = CommercialProposalRepository(session)
                    await cp_repo.update(proposal)
                
                analyzed_count += 1
            except Exception as e:
                logger.error(f"Error analyzing proposal {proposal.id}: {e}", exc_info=True)
        else:
            # Если рейтинг уже есть, но интегральный рейтинг не рассчитан, пересчитываем
            if proposal.integral_rating is None:
                integral_rating = calculate_integral_rating(
                    proposal.product_price,
                    proposal.delivery_cost,
                    proposal.supplier_rating,
                    proposal.other_conditions
                )
                proposal.integral_rating = integral_rating
                
                async with async_session_maker() as session:
                    cp_repo = CommercialProposalRepository(session)
                    await cp_repo.update(proposal)
    
    # Получаем обновленные данные
    async with async_session_maker() as session:
        cp_repo = CommercialProposalRepository(session)
        proposals = await cp_repo.get_all(user_id=db_user.id, limit=100)
    
    # Сортируем по интегральному рейтингу (от большего к меньшему)
    proposals_sorted = sorted(proposals, key=lambda x: x.integral_rating or 0, reverse=True)
    
    # Формируем отчет
    separator = format_separator(30)
    text = "📊 <b>Отчет сравнения коммерческих предложений</b>\n\n"
    text += f"{separator}\n"
    text += f"Всего КП: <code>{len(proposals_sorted)}</code>\n"
    if analyzed_count > 0:
        text += f"Проанализировано новых: <code>{analyzed_count}</code>\n"
    text += f"{separator}\n\n"
    
    for idx, prop in enumerate(proposals_sorted, 1):
        total_cost = prop.product_price + (prop.delivery_cost or 0)
        rating_emoji = "🟢" if (prop.integral_rating or 0) >= 70 else "🟡" if (prop.integral_rating or 0) >= 50 else "🔴"
        
        text += f"<b>{idx}. {prop.supplier_name}</b> {rating_emoji}\n"
        text += f"   💰 Цена товара: {format_rub(prop.product_price)}\n"
        text += f"   🚚 Доставка: {format_rub(prop.delivery_cost) if prop.delivery_cost else 'не указана'}\n"
        text += f"   💵 Итого: {format_rub(total_cost)}\n"
        
        if prop.items_count:
            text += f"   📦 Количество наименований: {prop.items_count}\n"
        else:
            text += f"   📦 Количество наименований: не определено\n"
        
        if prop.other_conditions:
            conditions_short = prop.other_conditions[:50] + "..." if len(prop.other_conditions) > 50 else prop.other_conditions
            text += f"   📋 Условия: {conditions_short}\n"
        
        if prop.supplier_rating is not None:
            text += f"   ⭐ Рейтинг поставщика: {prop.supplier_rating}/100\n"
            if prop.supplier_reliability_info:
                info_short = prop.supplier_reliability_info[:100] + "..." if len(prop.supplier_reliability_info) > 100 else prop.supplier_reliability_info
                text += f"   ℹ️ {info_short}\n"
        
        if prop.integral_rating is not None:
            text += f"   🎯 Интегральный рейтинг: {prop.integral_rating:.2f}/100\n"
        else:
            text += f"   🎯 Интегральный рейтинг: не рассчитан\n"
        
        text += f"\n{separator}\n\n"
    
    text += "💡 <b>Рекомендация:</b> Выберите КП с наивысшим интегральным рейтингом, учитывая все факторы."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить отчет", callback_data="cp:compare")],
        [InlineKeyboardButton(text="📋 Список КП", callback_data="cp:list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cp:menu")],
        get_main_menu_button()
    ])
    
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "cp:list")
async def list_proposals(query, db_user: User):
    """Показать список всех КП"""
    async with async_session_maker() as session:
        cp_repo = CommercialProposalRepository(session)
        proposals = await cp_repo.get_all(user_id=db_user.id, limit=100)
    
    if not proposals:
        await query.message.edit_text(
            "❌ <b>Нет коммерческих предложений</b>\n\n"
            "Загрузите первое коммерческое предложение.",
            parse_mode="HTML"
        )
        return
    
    separator = format_separator(30)
    text = f"{separator}\n"
    text += f"📋 <b>Список коммерческих предложений</b>\n"
    text += f"{separator}\n\n"
    text += f"Всего: <code>{len(proposals)}</code>\n\n"
    
    for idx, prop in enumerate(proposals[:20], 1):  # Показываем первые 20
        status = "✅" if prop.supplier_rating is not None else "⏳"
        text += f"<b>{idx}.</b> {status} <b>{prop.supplier_name}</b>\n"
        text += f"   💰 {format_rub(prop.product_price)}"
        if prop.items_count:
            text += f" | 📦 {prop.items_count} наименований"
        if prop.integral_rating:
            text += f" | 🎯 <code>{prop.integral_rating:.1f}</code>/100"
        text += "\n\n"
    
    if len(proposals) > 20:
        text += f"{separator}\n"
        text += f"... и еще <code>{len(proposals) - 20}</code> КП\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Сформировать отчет", callback_data="cp:compare")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cp:menu")],
        get_main_menu_button()[0]
    ])
    
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "cp:menu")
async def back_to_cp_menu(query, db_user: User, state: FSMContext):
    """Вернуться в меню КП"""
    await query.answer()
    await show_cp_menu(query.message, db_user, state)


@router.callback_query(F.data == "cp:clear_all")
async def clear_all_proposals(query, db_user: User, state: FSMContext):
    """Очистить все КП пользователя"""
    await query.answer("🗑️ Удаляю все КП...")
    
    try:
        async with async_session_maker() as session:
            cp_repo = CommercialProposalRepository(session)
            deleted_count = await cp_repo.delete_all_by_user(db_user.id)
        
        await query.message.edit_text(
            f"✅ <b>Все КП удалены</b>\n\n"
            f"Удалено КП: {deleted_count}\n\n"
            f"Вы можете загрузить новые коммерческие предложения.",
            parse_mode="HTML"
        )
        
        await state.clear()
        
        # Показываем меню для загрузки новых КП
        await query.message.answer(
            "📎 <b>Загрузите файл коммерческого предложения</b> (PDF, DOCX, DOC, TXT, RTF, Excel):",
            parse_mode="HTML"
        )
        await state.set_state(CommercialProposalStates.uploading_proposal)
        
    except Exception as e:
        logger.error(f"Error clearing proposals: {e}", exc_info=True)
        await query.message.edit_text(
            f"❌ <b>Ошибка при удалении КП</b>\n\n"
            f"Ошибка: {str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "cp:start_new")
async def start_new_proposals(query, db_user: User, state: FSMContext):
    """Начать загрузку новых КП"""
    await query.answer()
    await state.clear()
    
    await query.message.edit_text(
        "📎 <b>Загрузите файл коммерческого предложения</b>\n\n"
        "Поддерживаемые форматы: PDF, DOCX, DOC, TXT, RTF, Excel (XLSX, XLS)",
        parse_mode="HTML"
    )
    await state.set_state(CommercialProposalStates.uploading_proposal)

