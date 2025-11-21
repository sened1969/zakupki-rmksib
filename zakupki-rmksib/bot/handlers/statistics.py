"""Обработчики для статистики"""
from aiogram import Router, F
from aiogram.types import Message
from database.models import User
from database import async_session_maker, LotRepository, SupplierRepository, UserRepository
from database.repositories.commercial_proposal_repository import CommercialProposalRepository
from sqlalchemy import func, select
from utils.formatters import format_rub, format_separator, format_number

router = Router()


# Обработчик статистики регистрируется раньше обработчиков с FSM состояниями
# чтобы не перехватываться ими
@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message, db_user: User) -> None:
    """Показать общую статистику"""
    async with async_session_maker() as session:
        lot_repo = LotRepository(session)
        supplier_repo = SupplierRepository(session)
        user_repo = UserRepository(session)
        cp_repo = CommercialProposalRepository(session)
        
        all_lots = await lot_repo.get_all(limit=10000)
        all_suppliers = await supplier_repo.get_all(limit=10000)
        all_users = await user_repo.get_all_active(limit=10000)
        all_cps = await cp_repo.get_all(limit=10000)
    
    # Подсчитываем статистику лотов
    total_lots = len(all_lots)
    active_lots = len([l for l in all_lots if l.status == "active"])
    closed_lots = len([l for l in all_lots if l.status == "closed"])
    
    # Статистика по статусам просмотра
    not_viewed_lots = len([l for l in all_lots if (l.review_status or "not_viewed") == "not_viewed"])
    in_work_lots = len([l for l in all_lots if l.review_status == "in_work"])
    rejected_lots = len([l for l in all_lots if l.review_status == "rejected"])
    
    total_budget = sum(float(lot.budget) for lot in all_lots if lot.budget)
    active_budget = sum(float(lot.budget) for lot in all_lots if lot.status == "active" and lot.budget)
    
    # Статистика поставщиков
    total_suppliers = len(all_suppliers)
    rated_suppliers = len([s for s in all_suppliers if s.reliability_rating and s.reliability_rating > 0])
    
    # Статистика пользователей
    total_users = len(all_users)
    admins = len([u for u in all_users if u.role == "admin"])
    managers = len([u for u in all_users if u.role == "manager"])
    
    # Статистика коммерческих предложений
    total_cps = len(all_cps)
    analyzed_cps = len([cp for cp in all_cps if cp.supplier_rating is not None])
    total_cp_value = sum(float(cp.product_price) for cp in all_cps if cp.product_price)
    total_delivery_cost = sum(float(cp.delivery_cost) for cp in all_cps if cp.delivery_cost)
    total_cp_cost = total_cp_value + total_delivery_cost
    
    # Средние значения КП
    avg_cp_price = total_cp_value / total_cps if total_cps > 0 else 0
    avg_delivery = total_delivery_cost / total_cps if total_cps > 0 else 0
    avg_rating = sum(float(cp.integral_rating) for cp in all_cps if cp.integral_rating) / analyzed_cps if analyzed_cps > 0 else 0
    
    # Уникальные поставщики в КП
    unique_suppliers_cp = len(set(cp.supplier_name for cp in all_cps if cp.supplier_name))
    
    text = "📊 <b>Общая статистика</b>\n\n"
    separator = format_separator(25)
    
    # Статистика лотов
    text += f"{separator}\n"
    text += "📋 <b>Лоты</b>\n"
    text += f"{separator}\n"
    text += f"  • Всего: {format_number(total_lots)}\n"
    text += f"  • Активных: {format_number(active_lots)} 🟢\n"
    text += f"  • Закрытых: {format_number(closed_lots)} 🔴\n"
    text += f"\n  <b>Статусы просмотра:</b>\n"
    text += f"  • Не просмотрено: {format_number(not_viewed_lots)} 👁\n"
    text += f"  • В работе: {format_number(in_work_lots)} ✅\n"
    text += f"  • Отказ: {format_number(rejected_lots)} ❌\n"
    if total_budget > 0:
        text += f"\n  • Общий бюджет: {format_rub(total_budget)}\n"
        text += f"  • Бюджет активных: {format_rub(active_budget)}\n"
    text += "\n"
    
    # Статистика коммерческих предложений
    text += f"{separator}\n"
    text += "📄 <b>Коммерческие предложения</b>\n"
    text += f"{separator}\n"
    text += f"  • Всего КП: {format_number(total_cps)}\n"
    text += f"  • Проанализировано: {format_number(analyzed_cps)}\n"
    text += f"  • Уникальных поставщиков: {format_number(unique_suppliers_cp)}\n"
    if total_cp_value > 0:
        text += f"  • Общая стоимость товаров: {format_rub(total_cp_value)}\n"
        if total_delivery_cost > 0:
            text += f"  • Общая стоимость доставки: {format_rub(total_delivery_cost)}\n"
            text += f"  • Итого с доставкой: {format_rub(total_cp_cost)}\n"
        if avg_cp_price > 0:
            text += f"  • Средняя цена КП: {format_rub(avg_cp_price)}\n"
        if avg_delivery > 0:
            text += f"  • Средняя доставка: {format_rub(avg_delivery)}\n"
        if avg_rating > 0:
            text += f"  • Средний рейтинг: {format_number(avg_rating)}/100\n"
    text += "\n"
    
    # Статистика поставщиков
    text += f"{separator}\n"
    text += "🚛 <b>Поставщики</b>\n"
    text += f"{separator}\n"
    text += f"  • Всего: {format_number(total_suppliers)}\n"
    text += f"  • С рейтингом: {format_number(rated_suppliers)}\n"
    text += "\n"
    
    # Статистика пользователей
    text += f"{separator}\n"
    text += "👥 <b>Пользователи</b>\n"
    text += f"{separator}\n"
    text += f"  • Всего: {format_number(total_users)}\n"
    text += f"  • Администраторов: {format_number(admins)} 👑\n"
    text += f"  • Менеджеров: {format_number(managers)} 👤\n"
    
    await message.answer(text, parse_mode="HTML")

