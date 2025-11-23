"""Обработчики для работы с поставщиками"""
from aiogram import Router, F
from aiogram.types import Message
from database.models import User, Supplier
from database import async_session_maker, SupplierRepository

router = Router()


@router.message(F.text == "🚛 Поставщики")
async def show_suppliers(message: Message, db_user: User) -> None:
    """Показать список поставщиков"""
    async with async_session_maker() as session:
        supplier_repo = SupplierRepository(session)
        suppliers = await supplier_repo.get_all(limit=50)
    
    if not suppliers:
        await message.answer(
            "📭 База поставщиков пока пуста.\n\n"
            "Добавьте поставщиков вручную через административные команды."
        )
        return
    
    text = f"🚛 <b>База поставщиков ({len(suppliers)}):</b>\n\n"
    
    for idx, supplier in enumerate(suppliers[:15], 1):
        stars = "⭐" * min(supplier.reliability_rating, 5)
        text += f"{idx}. <b>{supplier.name}</b>\n"
        text += f"   {stars} (рейтинг: {supplier.reliability_rating})\n"
        text += f"   📧 {supplier.contact_email} | 📱 {supplier.contact_phone}\n"
        text += f"   🆔 ИНН: {supplier.inn}\n\n"
    
    if len(suppliers) > 15:
        text += f"... и еще {len(suppliers) - 15} поставщиков"
    
    await message.answer(text, parse_mode="HTML")























