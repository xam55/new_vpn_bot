from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F
from aiogram.fsm.context import FSMContext

from src.handlers.admin import admin_router
from src.services import get_session, UserDAO


@admin_router.message(Command("admin"))
@admin_router.message(F.text.startswith("👑"))
async def admin_entry(message: Message, state: FSMContext):
    async for session in get_session():
        user = await UserDAO.get_by_telegram_id(session, message.from_user.id)
        if not user or not user.is_admin:
            await message.answer("❌ У вас нет прав администратора")
            return

    from src.handlers.admin.panel import show_admin_panel
    await show_admin_panel(message, state)
