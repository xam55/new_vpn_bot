from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.config import config
from src.services import PaymentDAO, get_session

router = Router()


@router.message(Command("check"))
@router.message(F.text == "✅ Подтверждения")
async def cmd_check_payments(message: Message, state: FSMContext):
    """Проверка платежей (для администраторов)"""

    # Проверяем права администратора
    if message.from_user.id not in config.bot.admin_ids:
        await message.answer("❌ У вас нет прав доступа")
        return

    async for session in get_session():
        pending_payments = await PaymentDAO.get_pending_payments(session)

        if not pending_payments:
            await message.answer(
                "📭 <b>Нет платежей для проверки</b>\n\n"
                "Все платежи обработаны."
            )
            return

        await message.answer(
            f"✅ <b>Платежи для проверки:</b> {len(pending_payments)}\n\n"
            "Используйте админ-панель для просмотра деталей."
        )