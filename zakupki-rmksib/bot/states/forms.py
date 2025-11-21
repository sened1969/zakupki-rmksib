from aiogram.fsm.state import State, StatesGroup

class LotStates(StatesGroup):
    viewing_lots = State()
    viewing_lot_detail = State()
    confirming_analysis = State()
    viewing_analysis = State()
    waiting_decision = State()

class SupplierSearchStates(StatesGroup):
    selecting_search_level = State()
    searching = State()
    viewing_suppliers = State()
    selecting_suppliers = State()
    confirming_selection = State()

class RFQStates(StatesGroup):
    """Состояния для формирования запроса коммерческого предложения"""
    viewing_rfq_draft = State()  # Просмотр черновика запроса
    editing_rfq_text = State()  # Редактирование текста запроса
    confirming_send = State()  # Подтверждение отправки

class PreferenceStates(StatesGroup):
    selecting_action = State()
    setting_customers = State()
    setting_nomenclature = State()
    customer_menu = State()
    nomenclature_menu = State()
    # Email настройки
    email_setup = State()
    email_input = State()
    email_password_input = State()
    smtp_provider_selection = State()
    # Бюджет
    budget_setup = State()
    budget_min_input = State()
    budget_max_input = State()


class SupplierSearchStates(StatesGroup):
    """Состояния для поиска поставщиков"""
    choosing_method = State()  # Выбор метода поиска (Perplexity/Sniper)
    choosing_input = State()   # Выбор способа ввода (ручной/документ)
    manual_input = State()     # Ввод товара вручную
    waiting_document = State() # Ожидание загрузки документа
    processing = State()       # Обработка запроса


class DocumentationStates(StatesGroup):
    """Состояния для работы с документацией"""
    waiting_document = State()  # Ожидание загрузки документации
    selecting_lot = State()    # Выбор лота для загрузки документации
    waiting_manual_document = State()  # Ожидание загрузки документации без привязки к лоту


class ManualLotCreationStates(StatesGroup):
    """Состояния для создания лота вручную"""
    entering_title = State()      # Ввод названия лота
    entering_description = State() # Ввод описания
    entering_budget = State()     # Ввод бюджета
    entering_deadline = State()   # Ввод дедлайна
    entering_customer = State()   # Ввод заказчика
    confirming = State()          # Подтверждение создания


class CommercialProposalStates(StatesGroup):
    """Состояния для работы с коммерческими предложениями"""
    selecting_action = State()           # Выбор действия (загрузить КП, сформировать отчет)
    uploading_proposal = State()         # Загрузка файла КП
    entering_supplier_name = State()     # Ввод названия поставщика
    entering_supplier_inn = State()      # Ввод ИНН поставщика
    entering_product_price = State()     # Ввод цены товара
    entering_delivery_cost = State()     # Ввод стоимости доставки
    entering_other_conditions = State()  # Ввод прочих условий
    confirming_proposal = State()        # Подтверждение сохранения КП
