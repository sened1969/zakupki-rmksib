from sqlalchemy import Integer, String, Boolean, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default='user')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    customers: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Список строк с названиями заказчиков
    nomenclature: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Список строк с названиями номенклатурных групп
    # Email настройки
    email_password: Mapped[str | None] = mapped_column(Text, nullable=True)  # Зашифрованный пароль
    smtp_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # yandex, gmail, mailru
    # Настройки бюджета
    budget_min: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Минимальная сумма в рублях
    budget_max: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Максимальная сумма в рублях

class Lot(Base):
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_name: Mapped[str] = mapped_column(String(100))
    lot_number: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    budget: Mapped[float] = mapped_column(Float)
    deadline: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50))  # Статус лота: active, closed, pending, rejected
    review_status: Mapped[str | None] = mapped_column(String(50), nullable=True, default="not_viewed")  # Статус просмотра: not_viewed, in_work, rejected
    owner_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    customer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nomenclature: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Документация
    documentation_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Путь к файлу документации
    documentation_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # Извлеченный текст из документации
    documentation_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)  # Флаг анализа документации
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Источник: 'parser', 'email', 'manual'
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # URL страницы лота на площадке закупок

class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    inn: Mapped[str] = mapped_column(String(12), unique=True)
    contact_email: Mapped[str] = mapped_column(String(255))
    contact_phone: Mapped[str] = mapped_column(String(20))
    reliability_rating: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CommercialProposal(Base):
    __tablename__ = "commercial_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lot_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("lots.id"), nullable=True)  # Привязка к лоту (опционально)
    supplier_name: Mapped[str] = mapped_column(String(255))  # Название поставщика
    supplier_inn: Mapped[str | None] = mapped_column(String(12), nullable=True)  # ИНН поставщика
    proposal_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Путь к файлу КП
    proposal_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # Текст КП (извлеченный из файла)
    product_price: Mapped[float] = mapped_column(Float)  # Цена товара
    delivery_cost: Mapped[float | None] = mapped_column(Float, nullable=True)  # Стоимость доставки
    other_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)  # Прочие условия
    items_count: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Количество наименований товара в документе
    supplier_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Рейтинг поставщика (от LLM, 0-100)
    supplier_reliability_info: Mapped[str | None] = mapped_column(Text, nullable=True)  # Информация о надежности поставщика от LLM
    integral_rating: Mapped[float | None] = mapped_column(Float, nullable=True)  # Интегральный рейтинг КП
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))  # Кто создал КП
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Когда был проведен анализ
