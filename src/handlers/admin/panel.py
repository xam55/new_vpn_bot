from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.handlers.admin import admin_router
from src.config import config
from src.states.admin_states import AdminPanelStates
from src.keyboards.admin import (
    get_admin_panel_keyboard,
    get_admin_confirmation_keyboard
)
from src.services.database import get_session
from src.services.dao import PaymentDAO
from src.models.payment import Payment
from src.models.user import User

router = admin_router


# ===================== HELPERS =====================

def render_payment(payment: Payment, index: int, total: int) -> str:
    user = payment.user

    username = f"@{user.username}" if user.username else "без username"
    full_name = user.full_name or "Без имени"

    return (
        "💰 <b>Платёж на подтверждение</b>\n\n"
        f"👤 Пользователь: {full_name} ({username})\n"
        f"🆔 TG ID: <code>{user.telegram_id}</code>\n"
        f"💳 Payment ID: <code>{payment.payment_id}</code>\n"
        f"💰 Сумма: {payment.amount}₽\n"
        f"📌 Статус: {payment.status}\n\n"
        f"📦 Платёж {index + 1} из {total}"
    )


# ===================== ENTRY =====================

@router.message(Command("admin"))
async def open_admin_panel(message: Message, state: FSMContext):
    if message.from_user.id not in config.bot.admin_ids:
        await message.answer("❌ Нет прав администратора")
        return

    await state.clear()
    await state.set_state(AdminPanelStates.main_menu)

    await message.answer(
        "👑 <b>Админ-панель</b>\n\nВыберите раздел:",
        reply_markup=get_admin_panel_keyboard()
    )


# ===================== CONFIRMATIONS =====================

@router.callback_query(F.data == "admin_confirmations")
async def open_confirmations(callback: CallbackQuery, state: FSMContext):
    async for session in get_session():
        result = await session.execute(
            select(Payment)
            .where(Payment.status == "paid")
            .options(selectinload(Payment.user))  # 🔥 КЛЮЧ
            .order_by(Payment.created_at)
        )
        payments = list(result.scalars().all())

    if not payments:
        await callback.answer("📭 Нет ожидающих платежей", show_alert=True)
        return

    await state.set_state(AdminPanelStates.confirmations_list)
    await state.update_data(payments=payments, index=0)

    await callback.message.edit_text(
        render_payment(payments[0], 0, len(payments)),
        reply_markup=get_admin_confirmation_keyboard()
    )
    await callback.answer()


@router.callback_query(
    AdminPanelStates.confirmations_list,
    F.data.in_(["admin_next", "admin_prev"])
)
async def navigate_payments(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payments = data["payments"]
    index = data["index"]

    if callback.data == "admin_next" and index < len(payments) - 1:
        index += 1
    elif callback.data == "admin_prev" and index > 0:
        index -= 1

    await state.update_data(index=index)

    await callback.message.edit_text(
        render_payment(payments[index], index, len(payments)),
        reply_markup=get_admin_confirmation_keyboard()
    )
    await callback.answer()


# ===================== CONFIRM =====================

@router.callback_query(
    AdminPanelStates.confirmations_list,
    F.data == "admin_confirm"
)
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payments = data["payments"]
    index = data["index"]

    payment = payments[index]

    async for session in get_session():
        await PaymentDAO.confirm_payment(
            session=session,
            payment_id=payment.id,
            admin_id=callback.from_user.id
        )

    payments.pop(index)

    if not payments:
        await state.clear()
        await callback.message.edit_text("✅ Все платежи подтверждены")
        return

    index = min(index, len(payments) - 1)
    await state.update_data(payments=payments, index=index)

    await callback.message.edit_text(
        render_payment(payments[index], index, len(payments)),
        reply_markup=get_admin_confirmation_keyboard()
    )
    await callback.answer("✅ Платёж подтверждён")


# ===================== REJECT =====================

@router.callback_query(
    AdminPanelStates.confirmations_list,
    F.data == "admin_reject"
)
async def reject_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payments = data["payments"]
    index = data["index"]

    payment = payments[index]

    async for session in get_session():
        await PaymentDAO.reject_payment(
            session=session,
            payment_id=payment.id,
            admin_id=callback.from_user.id
        )

    payments.pop(index)

    if not payments:
        await state.clear()
        await callback.message.edit_text("📭 Нет ожидающих платежей")
        return

    index = min(index, len(payments) - 1)
    await state.update_data(payments=payments, index=index)

    await callback.message.edit_text(
        render_payment(payments[index], index, len(payments)),
        reply_markup=get_admin_confirmation_keyboard()
    )
    await callback.answer("❌ Платёж отклонён")


# ===================== BACK =====================

@router.callback_query(F.data == "admin_back")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👑 <b>Админ-панель</b>\n\nВыберите раздел:",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()
