from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.config import config
from src.keyboards.admin import get_admin_panel_keyboard
from src.states.admin_states import AdminPanelStates

router = Router()


@router.message(Command("admin"))
@router.message(F.text == "👑 Админ-панель")
async def cmd_admin_panel(message: Message, state: FSMContext):
    """Открыть админ-панель"""

    # Проверяем права администратора
    if message.from_user.id not in config.bot.admin_ids:
        await message.answer("❌ У вас нет прав доступа к админ-панели")
        return

    await state.clear()
    await state.set_state(AdminPanelStates.main_menu)

    await message.answer(
        "👑 <b>Админ-панель VPN Bot</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data == "admin_back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "👑 <b>Админ-панель VPN Bot</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=get_admin_panel_keyboard()
    )
    await state.set_state(AdminPanelStates.main_menu)
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в меню админ-панели"""
    await callback.message.edit_text(
        "👑 <b>Админ-панель VPN Bot</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=get_admin_panel_keyboard()
    )
    await state.set_state(AdminPanelStates.main_menu)
    await callback.answer()


@router.callback_query(F.data == "admin_confirmations")
async def show_confirmations(callback: CallbackQuery, state: FSMContext):
    """Показать платежи для подтверждения"""

    if callback.from_user.id not in config.bot.admin_ids:
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    from src.services.database import PaymentDAO, get_session
    from src.keyboards.admin import get_admin_confirmations_keyboard

    async for session in get_session():
        pending_payments = await PaymentDAO.get_pending_payments(session)

        if not pending_payments:
            await callback.message.edit_text(
                "📭 <b>Нет ожидающих подтверждений</b>\n\n"
                "Все платежи обработаны.",
                reply_markup=get_admin_confirmations_keyboard([])
            )
        else:
            await callback.message.edit_text(
                f"✅ <b>Платежи для подтверждения</b>\n\n"
                f"Найдено: {len(pending_payments)} платежей",
                reply_markup=get_admin_confirmations_keyboard(pending_payments)
            )

    await state.set_state(AdminPanelStates.confirmations_list)
    await callback.answer()