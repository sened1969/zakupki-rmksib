"""Handlers for supplier search functionality"""
import logging
import aiohttp
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.forms import SupplierSearchStates
from bot.keyboards.inline import get_supplier_search_menu, get_search_input_menu, get_after_search_menu
from services.ai.perplexity import search_suppliers_perplexity
from services.search.sniper_search import SniperSearchService
from config.settings import settings
from utils.telegram_helpers import send_long_message

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.in_(["Поиск Поставщиков", "🔍 Поиск Поставщиков"]))
async def supplier_search_start(message: Message, state: FSMContext):
    """Начало процесса поиска поставщиков по кнопке"""
    await state.set_state(SupplierSearchStates.choosing_method)
    await message.answer(
        "<b>Поиск Поставщиков</b>\n\n"
        "Выберите метод поиска:",
        reply_markup=get_supplier_search_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("search:"))
async def process_search_method(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора метода поиска"""
    method = callback.data.split(":")[1]
    
    if method == "back":
        await state.clear()
        await callback.message.edit_text(
            "Поиск отменён",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Сохраняем выбранный метод
    await state.update_data(search_method=method)
    await state.set_state(SupplierSearchStates.choosing_input)
    
    method_name = "Perplexity AI" if method == "perplexity" else "Sniper Search"
    await callback.message.edit_text(
        f"✅ Выбран метод: <b>{method_name}</b>\n\n"
        "Как вы хотите ввести данные для поиска?",
        reply_markup=get_search_input_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("input:"))
async def process_input_method(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора способа ввода"""
    input_type = callback.data.split(":")[1]
    
    if input_type == "back":
        await state.set_state(SupplierSearchStates.choosing_method)
        await callback.message.edit_text(
            "<b>Поиск Поставщиков</b>\n\n"
            "Выберите метод поиска:",
            reply_markup=get_supplier_search_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    if input_type == "manual":
        await state.set_state(SupplierSearchStates.manual_input)
        await callback.message.edit_text(
            "✍️ Введите название товара для поиска:\n\n"
            "Например: <i>Болт М10х50</i> или <i>Перчатки рабочие</i>",
            parse_mode="HTML"
        )
    elif input_type == "upload":
        await state.set_state(SupplierSearchStates.waiting_document)
        await callback.message.edit_text(
            "Загрузите документ с перечнем товаров\n\n"
            "Поддерживаемые форматы: PDF, DOCX, Excel",
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.message(SupplierSearchStates.manual_input)
async def process_manual_input(message: Message, state: FSMContext):
	"""Обработка ручного ввода товара"""
	# Проверяем, есть ли уже product_name в state (из анализа документации)
	data = await state.get_data()
	product_name = data.get("product_name", "")
	
	# Если product_name не был передан из анализа, используем текст сообщения
	if not product_name:
		product_name = message.text.strip()
		if not product_name:
			await message.answer("❌ Пожалуйста, введите корректное название товара")
			return
	
	search_method = data.get("search_method", "perplexity")
	
	await state.set_state(SupplierSearchStates.processing)
	await message.answer(
		f"⏳ Ищу поставщиков для товара: <b>{product_name}</b>\n"
		f"Метод: <b>{'Perplexity AI' if search_method == 'perplexity' else 'Sniper Search'}</b>\n\n"
		"Пожалуйста, подождите...",
		parse_mode="HTML"
	)
	
	try:
		if search_method == "perplexity":
			# Поиск через Perplexity AI
			logger.info(f"Searching suppliers via Perplexity for: {product_name}")
			try:
				result = await search_suppliers_perplexity(product_name)
			except RuntimeError as e:
				# Пробрасываем RuntimeError с деталями дальше для более подробной обработки
				logger.error(f"Detailed Perplexity error: {str(e)}")
				raise
			
			if result:
				# Форматируем результат
				response_text = (
					f"🔍 <b>Результаты поиска поставщиков</b>\n\n"
					f"<b>Товар:</b> {product_name}\n"
					f"<b>Метод:</b> Perplexity AI\n\n"
					f"<b>Найденные поставщики:</b>\n\n{result}"
				)
			else:
				response_text = (
					f"❌ Не удалось найти поставщиков для товара: <b>{product_name}</b>\n\n"
					"Попробуйте:\n"
					"- Уточнить название товара\n"
					"- Использовать другой метод поиска\n"
					"- Проверить правильность написания"
				)
			
		elif search_method == "sniper":
			# Поиск через Sniper Search
			logger.info(f"Searching suppliers via Sniper Search for: {product_name}")
			
			if not settings.SNIPER_SEARCH_BASE_URL:
				response_text = (
					"❌ Sniper Search API не настроен.\n\n"
					"Обратитесь к администратору для настройки:\n"
					"• SNIPER_SEARCH_BASE_URL в .env\n"
					"• SNIPER_SEARCH_API_TOKEN в .env\n\n"
					"См. SNIPER_SEARCH_SETUP.md для инструкций."
				)
			elif not settings.SNIPER_SEARCH_API_TOKEN:
				response_text = (
					"❌ Sniper Search API токен не настроен.\n\n"
					"Для работы Sniper Search необходимо:\n"
					"1. Получить API токен на sniper-search.ru\n"
					"2. Добавить в .env:\n"
					"   SNIPER_SEARCH_API_TOKEN=your_token_here\n\n"
					"См. SNIPER_SEARCH_SETUP.md для подробных инструкций.\n\n"
					"💡 Используйте метод Perplexity AI для поиска."
				)
			else:
				try:
					# Передаем API токен из настроек
					async with SniperSearchService(api_token=settings.SNIPER_SEARCH_API_TOKEN) as sniper:
						task_result = await sniper.search_suppliers(product_name)
						task_id = task_result.get("task_id")
						
						if task_id:
							response_text = (
								f"✅ <b>Задача поиска создана</b>\n\n"
								f"<b>Товар:</b> {product_name}\n"
								f"<b>Метод:</b> Sniper Search\n"
								f"<b>ID задачи:</b> {task_id}\n\n"
								"⏳ Поиск поставщиков выполняется в фоновом режиме.\n"
								"Результаты будут доступны через некоторое время.\n\n"
								"Для получения результатов используйте API Sniper Search с указанным task_id."
							)
						else:
							response_text = (
								f"❌ Не удалось создать задачу поиска для: <b>{product_name}</b>\n\n"
								"Попробуйте использовать метод Perplexity AI."
							)
				except (aiohttp.ClientError, OSError, ConnectionError) as e:
					# Ошибки сети/DNS - автоматический fallback на Perplexity
					error_msg = str(e)
					logger.warning(f"Sniper Search недоступен ({error_msg}), переключаюсь на Perplexity")
					
					# Автоматический fallback на Perplexity
					try:
						result = await search_suppliers_perplexity(product_name)
						if result:
							response_text = (
								f"⚠️ <b>Sniper Search недоступен</b>\n"
								f"Использую <b>Perplexity AI</b> для поиска\n\n"
								f"🔍 <b>Результаты поиска поставщиков</b>\n\n"
								f"<b>Товар:</b> {product_name}\n"
								f"<b>Метод:</b> Perplexity AI (fallback)\n\n"
								f"<b>Найденные поставщики:</b>\n\n{result}"
							)
						else:
							response_text = (
								f"❌ <b>Sniper Search недоступен</b>\n\n"
								f"Проблема: {error_msg}\n\n"
								f"Попытка поиска через Perplexity AI не дала результатов для: <b>{product_name}</b>\n\n"
								"Возможные причины:\n"
								"• Проблемы с сетью или DNS\n"
								"• Sniper Search API временно недоступен\n"
								"• Неверное название товара\n\n"
								"Попробуйте:\n"
								"• Проверить интернет-соединение\n"
								"• Уточнить название товара\n"
								"• Попробовать позже"
							)
					except Exception as perplexity_error:
						logger.error(f"Perplexity fallback also failed: {perplexity_error}")
						response_text = (
							f"❌ <b>Ошибка при поиске поставщиков</b>\n\n"
							f"<b>Sniper Search:</b> {error_msg}\n"
							f"<b>Perplexity AI:</b> {str(perplexity_error)}\n\n"
							"Оба метода поиска недоступны.\n\n"
							"Возможные причины:\n"
							"• Проблемы с сетью или DNS\n"
							"• API сервисы временно недоступны\n"
							"• Проблемы с API ключами\n\n"
							"Попробуйте позже или обратитесь к администратору."
						)
				except Exception as e:
					# Другие ошибки Sniper Search
					logger.error(f"Sniper Search error: {e}")
					error_msg = str(e)
					
					# Проверяем ошибки авторизации
					if "401" in error_msg or "Unauthorized" in error_msg or "authorization" in error_msg.lower():
						response_text = (
							f"❌ <b>Ошибка авторизации Sniper Search API</b>\n\n"
							f"🔑 Проблема с API токеном:\n\n"
							"• API токен не установлен в .env файле\n"
							"• API токен неверный или устарел\n"
							"• API токен не имеет нужных прав доступа\n\n"
							"📝 Решение:\n"
							"1. Проверьте файл .env\n"
							"2. Убедитесь, что SNIPER_SEARCH_API_TOKEN установлен\n"
							"3. Получите новый токен на sniper-search.ru\n"
							"4. См. SNIPER_SEARCH_SETUP.md для инструкций\n\n"
							"💡 Альтернатива:\n"
							"Используйте метод <b>Perplexity AI</b> для поиска поставщиков"
						)
					# Проверяем, можно ли использовать Perplexity как fallback
					elif "getaddrinfo failed" in error_msg or "Cannot connect" in error_msg:
						# Сетевая ошибка - пробуем Perplexity
						try:
							result = await search_suppliers_perplexity(product_name)
							if result:
								response_text = (
									f"⚠️ <b>Sniper Search недоступен</b>\n"
									f"Использую <b>Perplexity AI</b> для поиска\n\n"
									f"🔍 <b>Результаты поиска поставщиков</b>\n\n"
									f"<b>Товар:</b> {product_name}\n"
									f"<b>Метод:</b> Perplexity AI (fallback)\n\n"
									f"<b>Найденные поставщики:</b>\n\n{result}"
								)
							else:
								response_text = (
									f"❌ Ошибка при обращении к Sniper Search API:\n"
									f"{error_msg}\n\n"
									"Попытка поиска через Perplexity AI не дала результатов.\n"
									"Попробуйте позже или используйте другой метод поиска."
								)
						except Exception:
							response_text = (
								f"❌ Ошибка при обращении к Sniper Search API:\n"
								f"{error_msg}\n\n"
								"Попробуйте использовать метод Perplexity AI."
							)
					else:
						response_text = (
							f"❌ Ошибка при обращении к Sniper Search API:\n"
							f"{error_msg}\n\n"
							"Попробуйте использовать метод Perplexity AI."
						)
		else:
			response_text = "❌ Неизвестный метод поиска"
		
		# Сохраняем данные поиска в state для дальнейшего использования
		await state.update_data(
			product_name=product_name,
			search_result=response_text,
			search_method=search_method
		)
		
		# Отправляем результат с кнопками действий
		# Используем send_long_message для разбиения длинных сообщений
		# Проверяем длину сообщения
		if len(response_text) > 4096:
			# Используем специальную функцию для длинных сообщений
			# Получаем bot из message
			from aiogram import Bot
			bot = message.bot
			await send_long_message(
				bot=bot,
				chat_id=message.chat.id,
				text=response_text,
				parse_mode="HTML",
				reply_markup=get_after_search_menu()
			)
		else:
			# Обычная отправка для коротких сообщений
			await message.answer(
				response_text,
				parse_mode="HTML",
				reply_markup=get_after_search_menu()
			)
		
	except Exception as e:
		logger.error(f"Error during supplier search: {e}", exc_info=True)
		error_msg = str(e)
		# Если это ошибка Perplexity API, показываем более понятное сообщение
		if "Perplexity API error" in error_msg or "authorization failed" in error_msg.lower():
			if "401" in error_msg or "authorization" in error_msg.lower():
				await message.answer(
					"❌ <b>Ошибка авторизации Perplexity API</b>\n\n"
					"🔑 Проблема с API ключом:\n\n"
					"• API ключ не установлен в .env файле\n"
					"• API ключ неверный или устарел\n"
					"• API ключ не имеет нужных прав доступа\n\n"
					"📝 Решение:\n"
					"1. Проверьте файл .env\n"
					"2. Убедитесь, что PERPLEXITY_API_KEY установлен\n"
					"3. Ключ должен начинаться с 'pplx-'\n"
					"4. Получите новый ключ на https://www.perplexity.ai/\n\n"
					"💡 Альтернатива:\n"
					"Используйте метод <b>Sniper Search</b> для поиска поставщиков",
					parse_mode="HTML"
				)
			else:
				error_msg_clean = error_msg.replace("Perplexity API error: ", "")
				await message.answer(
					f"❌ <b>Ошибка Perplexity API:</b>\n\n"
					f"{error_msg_clean}\n\n"
					"Возможные причины:\n"
					"• Проблема с API ключом\n"
					"• Превышен лимит запросов\n"
					"• Неверный формат запроса\n\n"
					"Попробуйте:\n"
					"• Использовать метод Sniper Search\n"
					"• Упростить название товара\n"
					"• Попробовать позже",
					parse_mode="HTML"
				)
		else:
			await message.answer(
				f"❌ Произошла ошибка при поиске поставщиков:\n\n"
				f"{error_msg}\n\n"
				"Попробуйте позже или используйте другой метод поиска.",
				parse_mode="HTML"
			)
	finally:
		# НЕ очищаем state здесь, т.к. данные нужны для формирования RFQ
		# await state.clear()
		pass

@router.message(SupplierSearchStates.waiting_document)
async def process_document_upload(message: Message, state: FSMContext, bot: Bot):
    """Обработка загруженного документа"""
    if not message.document:
        await message.answer(
            "❌ Пожалуйста, отправьте документ (PDF, DOCX или Excel)"
        )
        return
    
    data = await state.get_data()
    search_method = data.get("search_method", "perplexity")
    
    await state.set_state(SupplierSearchStates.processing)
    status_msg = await message.answer(
        f"Документ получен: <b>{message.document.file_name}</b>\n"
        f"Метод: <b>{'Perplexity AI' if search_method == 'perplexity' else 'Sniper Search'}</b>\n\n"
        "⏳ Обрабатываю документ...",
        parse_mode="HTML"
    )
    
    try:
        # Проверяем формат файла
        from services.documentation.processor import is_supported_format, save_documentation_file, extract_text_from_file
        from pathlib import Path
        
        filename = message.document.file_name
        if not is_supported_format(filename):
            await status_msg.edit_text(
                f"❌ Неподдерживаемый формат файла: {filename}\n\n"
                f"Поддерживаемые форматы: PDF, DOCX, Excel (XLSX, XLS)"
            )
            await state.clear()
            return
        
        # Скачиваем файл
        # В aiogram 3.x правильный способ - использовать download() напрямую с объектом документа
        import io
        buffer = io.BytesIO()
        await bot.download(message.document, destination=buffer)
        file_bytes = buffer.getvalue()
        buffer.close()
        
        if not file_bytes:
            await status_msg.edit_text(
                "❌ Получен пустой файл. Попробуйте загрузить файл еще раз."
            )
            await state.clear()
            return
        
        # Сохраняем файл
        file_path = await save_documentation_file(file_bytes, filename)
        file_ext = Path(file_path).suffix.lower()
        
        # Обрабатываем файл в зависимости от типа
        products = []
        
        if file_ext in {'.xlsx', '.xls'}:
            # Парсим Excel файл
            from services.suppliers.excel_parser import extract_products_from_excel
            products = await extract_products_from_excel(file_path)
            
            if not products:
                await status_msg.edit_text(
                    f"❌ Не удалось извлечь товары из Excel файла.\n\n"
                    f"Убедитесь, что файл содержит таблицу с товарами.\n"
                    f"Ожидаемые столбцы: 'Номенклатура' или 'Наименование'"
                )
                await state.clear()
                return
            
            await status_msg.edit_text(
                f"✅ Найдено товаров: <b>{len(products)}</b>\n\n"
                f"⏳ Ищу поставщиков для каждого товара...",
                parse_mode="HTML"
            )
        else:
            # Для PDF/DOCX извлекаем текст и используем LLM для извлечения товаров
            await status_msg.edit_text(
                "⏳ Извлекаю текст из документа...",
                parse_mode="HTML"
            )
            
            text = await extract_text_from_file(file_path)
            if not text or text.startswith("[Ошибка"):
                await status_msg.edit_text(
                    f"❌ Не удалось извлечь текст из документа.\n\n"
                    f"Ошибка: {text}"
                )
                await state.clear()
                return
            
            # Используем LLM для извлечения списка товаров из текста
            await status_msg.edit_text(
                "⏳ Анализирую документ и извлекаю список товаров...",
                parse_mode="HTML"
            )
            
            from services.ai.perplexity import ask_perplexity
            import json
            import re
            
            llm_prompt = (
                f"Извлеки список товаров из следующего документа.\n\n"
                f"Документ:\n{text[:5000]}\n\n"
                f"Требования:\n"
                f"- Найди все товары/номенклатуру из документа\n"
                f"- Для каждого товара укажи полное наименование\n"
                f"- Если указано количество, укажи его (только число, без единиц измерения)\n"
                f"- Если указаны единицы измерения (шт., кг., м., л. и т.д.), укажи их отдельно\n"
                f"- Верни результат в формате JSON массива:\n"
                f'[{{"name": "Название товара", "quantity": "Количество (только число, если есть)", "unit": "Единица измерения (шт., кг., м. и т.д., если есть)"}}]\n\n'
                f"Примеры единиц измерения: шт., штук, кг., килограмм, г., грамм, т., тонн, м., метр, см., сантиметр, мм., миллиметр, л., литр, мл., миллилитр, м², м³, упак., упаковок, компл., комплект, пар, п.м., пог.м.\n\n"
                f"ВАЖНО: Верни ТОЛЬКО JSON массив, без дополнительного текста."
            )
            
            messages = [
                {"role": "system", "content": (
                    "Ты эксперт по извлечению данных из документов. "
                    "Твоя задача - извлечь список товаров из документа и вернуть его в формате JSON. "
                    "Отвечай ТОЛЬКО JSON массивом, без дополнительного текста."
                )},
                {"role": "user", "content": llm_prompt},
            ]
            
            try:
                llm_result = await ask_perplexity(messages, max_tokens=2000)
                
                # Пытаемся извлечь JSON из ответа
                json_match = re.search(r'\[.*\]', llm_result, re.DOTALL)
                if json_match:
                    products_json = json.loads(json_match.group())
                    products = [
                        {
                            "name": p.get("name", ""),
                            "code": None,
                            "row_number": idx + 1,
                            "quantity": p.get("quantity"),
                            "unit": p.get("unit")
                        }
                        for idx, p in enumerate(products_json) if p.get("name")
                    ]
                else:
                    # Если не удалось распарсить JSON, пытаемся извлечь товары вручную
                    logger.warning("Could not parse JSON from LLM response, trying manual extraction")
                    lines = llm_result.split('\n')
                    for line in lines:
                        if 'name' in line.lower() or 'товар' in line.lower():
                            # Простая эвристика для извлечения названий
                            name_match = re.search(r'["\']([^"\']+)["\']', line)
                            if name_match:
                                products.append({
                                    "name": name_match.group(1),
                                    "code": None,
                                    "row_number": len(products) + 1,
                                    "quantity": None,
                                    "unit": None
                                })
            except Exception as e:
                logger.error(f"Error extracting products from document via LLM: {e}", exc_info=True)
                await status_msg.edit_text(
                    f"❌ Ошибка при извлечении товаров из документа.\n\n"
                    f"Попробуйте загрузить Excel файл с таблицей товаров."
                )
                await state.clear()
                return
        
        if not products:
            await status_msg.edit_text(
                f"❌ Не удалось найти товары в документе.\n\n"
                f"Убедитесь, что документ содержит перечень товаров."
            )
            await state.clear()
            return
        
        # Ищем поставщиков для каждого товара и группируем по email
        all_results = []
        suppliers_by_email = {}  # Словарь: email -> {supplier_info, products: [список товаров]}
        total_products = len(products)
        
        for idx, product in enumerate(products, 1):
            product_name = product["name"]
            quantity = product.get('quantity')
            unit = product.get('unit')
            if quantity and unit:
                quantity_info = f" (Количество: {quantity} {unit})"
            elif quantity:
                quantity_info = f" (Количество: {quantity})"
            elif unit:
                quantity_info = f" (Единица измерения: {unit})"
            else:
                quantity_info = ""
            
            # Обновляем статус
            try:
                await status_msg.edit_text(
                    f"⏳ Обрабатываю товар <b>{idx}/{total_products}</b>\n\n"
                    f"Товар: <b>{product_name[:50]}...</b>{quantity_info}\n\n"
                    f"Ищу поставщиков...",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            
            # Ищем поставщиков
            try:
                if search_method == "perplexity":
                    suppliers_result = await search_suppliers_perplexity(product_name, max_suppliers=10)
                elif search_method == "sniper":
                    from services.search.sniper_search import SniperSearchService
                    if settings.SNIPER_SEARCH_API_TOKEN:
                        async with SniperSearchService(api_token=settings.SNIPER_SEARCH_API_TOKEN) as sniper:
                            task_result = await sniper.search_suppliers(product_name)
                            task_id = task_result.get("task_id")
                            suppliers_result = (
                                f"✅ Задача поиска создана для товара: {product_name}\n"
                                f"ID задачи: {task_id}\n"
                                f"Результаты будут доступны через некоторое время."
                            )
                    else:
                        # Fallback на Perplexity
                        suppliers_result = await search_suppliers_perplexity(product_name, max_suppliers=10)
                else:
                    suppliers_result = await search_suppliers_perplexity(product_name, max_suppliers=10)
                
                all_results.append({
                    "product": product_name,
                    "quantity": product.get("quantity"),
                    "unit": product.get("unit"),
                    "code": product.get("code"),
                    "suppliers": suppliers_result
                })
                
                # Извлекаем email адреса из результата поиска для группировки
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                
                # Извлекаем информацию о поставщиках из текста результата
                supplier_lines = suppliers_result.split('\n')
                current_supplier = None
                
                for line in supplier_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Ищем строки с названием поставщика (обычно начинаются с цифры и точки)
                    if re.match(r'^\d+\.\s*<b>', line) or re.match(r'^\d+\.\s*[А-ЯЁA-Z]', line):
                        # Извлекаем название поставщика
                        name_match = re.search(r'<b>(.+?)</b>', line)
                        if not name_match:
                            # Пробуем без HTML тегов
                            name_match = re.search(r'^\d+\.\s*(.+?)(?:\s*\||$)', line)
                            if name_match:
                                name_match = type('obj', (object,), {'group': lambda self, n=1: name_match.group(1).strip()})()
                        
                        if name_match:
                            supplier_name_text = name_match.group(1).strip()
                            # Убираем HTML теги из названия
                            supplier_name_text = re.sub(r'<[^>]+>', '', supplier_name_text)
                            current_supplier = {
                                'name': supplier_name_text,
                                'email': None,
                                'website': None,
                                'phone': None
                            }
                    elif current_supplier:
                        # Ищем email в строке (учитываем HTML разметку)
                        # Убираем HTML теги для поиска
                        line_clean = re.sub(r'<[^>]+>', '', line)
                        
                        # Ищем email в строке
                        email_match = re.search(email_pattern, line_clean)
                        if email_match:
                            email = email_match.group().lower()
                            # Фильтруем некорректные email
                            if email and '@' in email and '.' in email.split('@')[1]:
                                current_supplier['email'] = email
                                
                                # Группируем поставщиков по email
                                if email not in suppliers_by_email:
                                    suppliers_by_email[email] = {
                                        'supplier': current_supplier.copy(),
                                        'products': []
                                    }
                                
                                # Добавляем товар к поставщику
                                product_info = {
                                    'name': product_name,
                                    'quantity': product.get('quantity'),
                                    'unit': product.get('unit'),
                                    'code': product.get('code')
                                }
                                # Проверяем, нет ли уже этого товара у поставщика
                                if not any(p['name'] == product_name for p in suppliers_by_email[email]['products']):
                                    suppliers_by_email[email]['products'].append(product_info)
                            
                        # Ищем сайт
                        website_match = re.search(r'https?://[^\s<]+', line)
                        if website_match and not current_supplier.get('website'):
                            website = website_match.group()
                            # Убираем закрывающие теги и пробелы
                            website = website.rstrip('</>').strip()
                            current_supplier['website'] = website
                            
                        # Ищем телефон
                        phone_match = re.search(r'[\+]?[0-9\s\-\(\)]{10,}', line_clean)
                        if phone_match and not current_supplier.get('phone'):
                            phone = phone_match.group().strip()
                            # Фильтруем слишком короткие или длинные номера
                            digits_only = re.sub(r'[^\d+]', '', phone)
                            if 10 <= len(digits_only) <= 15:
                                current_supplier['phone'] = phone
                
                # Если у текущего поставщика есть email, но он еще не добавлен в группировку
                if current_supplier and current_supplier.get('email'):
                    email = current_supplier['email']
                    if email not in suppliers_by_email:
                        suppliers_by_email[email] = {
                            'supplier': current_supplier.copy(),
                            'products': []
                        }
                    # Добавляем товар, если его еще нет
                    product_info = {
                        'name': product_name,
                        'quantity': product.get('quantity'),
                        'unit': product.get('unit'),
                        'code': product.get('code')
                    }
                    if not any(p['name'] == product_name for p in suppliers_by_email[email]['products']):
                        suppliers_by_email[email]['products'].append(product_info)
                
                # Логируем результаты группировки для отладки
                if suppliers_by_email:
                    logger.info(f"Grouped suppliers by email for product '{product_name}': {len(suppliers_by_email)} unique emails")
                    for email, info in list(suppliers_by_email.items())[:3]:
                        logger.debug(f"  {email}: {info['supplier'].get('name', 'Unknown')} - {len(info['products'])} products")
                
            except Exception as e:
                logger.error(f"Error searching suppliers for {product_name}: {e}", exc_info=True)
                all_results.append({
                    "product": product_name,
                    "quantity": product.get("quantity"),
                    "code": product.get("code"),
                    "suppliers": f"❌ Ошибка при поиске поставщиков: {str(e)[:100]}"
                })
        
        # Формируем итоговый отчет
        report_text = f"🔍 <b>Результаты поиска поставщиков</b>\n\n"
        report_text += f"Обработано товаров: <b>{total_products}</b>\n"
        report_text += f"Метод поиска: <b>{'Perplexity AI' if search_method == 'perplexity' else 'Sniper Search'}</b>\n"
        report_text += f"Найдено уникальных поставщиков (с email): <b>{len(suppliers_by_email)}</b>\n\n"
        report_text += f"{'='*40}\n\n"
        
        for idx, result in enumerate(all_results, 1):
            report_text += f"<b>Товар {idx}: {result['product']}</b>\n"
            if result.get('quantity') and result.get('unit'):
                report_text += f"Количество: {result['quantity']} {result['unit']}\n"
            elif result.get('quantity'):
                report_text += f"Количество: {result['quantity']}\n"
            elif result.get('unit'):
                report_text += f"Единица измерения: {result['unit']}\n"
            if result.get('code'):
                report_text += f"Код: {result['code']}\n"
            report_text += f"\n{result['suppliers']}\n\n"
            report_text += f"{'='*40}\n\n"
        
        # Сохраняем результаты в state для дальнейшего использования
        await state.update_data(
            search_results=all_results,
            search_method=search_method,
            total_products=total_products,
            products=products,  # Сохраняем список всех товаров
            suppliers_by_email=suppliers_by_email,  # Сохраняем группировку по email
            is_from_document=True  # Флаг, что поиск был выполнен через документ
        )
        
        # Отправляем отчет
        if len(report_text) > 4096:
            # Разбиваем на части
            await send_long_message(
                bot=bot,
                chat_id=message.chat.id,
                text=report_text,
                parse_mode="HTML",
                reply_markup=get_after_search_menu()
            )
        else:
            await status_msg.edit_text(
                report_text,
                parse_mode="HTML",
                reply_markup=get_after_search_menu()
            )
        
    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ Ошибка при обработке документа:\n\n"
            f"<code>{str(e)[:200]}</code>\n\n"
            f"Попробуйте загрузить файл еще раз или обратитесь к администратору.",
            parse_mode="HTML"
        )
        await state.clear()
