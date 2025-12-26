from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

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

from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = Router()


# ========= ВСПОМОГАТЕЛЬНОЕ =========

async def show_admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AdminPanelStates.main_menu)
    await message.answer(
        "👑 <b>Админ-панель VPN Bot</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=get_admin_panel_keyboard()
    )


def render_payment(payment: Payment, index: int, total: int) -> str:
    user = payment.user
    username = f"@{user.username}" if user.username else "без username"

    return (
        "💰 <b>Платёж на подтверждение</b>\n\n"
        f"👤 Пользователь: {user.full_name or 'Без имени'} ({username})\n"
        f"🆔 TG ID: <code>{user.telegram_id}</code>\n"
        f"💳 Payment ID: <code>{payment.payment_id}</code>\n"
        f"💰 Сумма: {payment.amount}₽\n\n"
        f"📦 Платёж {index + 1} из {total}"
    )


# ========= ПОДТВЕРЖДЕНИЯ =========



@router.callback_query(F.data == "admin_confirmations")
async def open_confirmations(callback: CallbackQuery, state: FSMContext):
    async for session in get_session():
        result = await session.execute(
            select(Payment)
            .where(Payment.status == "paid")
            .options(selectinload(Payment.user))  # 🔥 КЛЮЧЕВАЯ СТРОКА
        )
        payments = result.scalars().all()

    if not payments:
        await callback.message.edit_text(
            "📭 <b>Нет платежей на подтверждение</b>",
            reply_markup=get_admin_panel_keyboard()
        )
        await callback.answer()
        return

    await state.set_state(AdminPanelStates.confirmations_list)
    await state.update_data(payments=payments, index=0)

    await callback.message.edit_text(
        render_payment(payments[0], 0, len(payments)),
        reply_markup=get_admin_confirmation_keyboard()
    )
    await callback.answer()


@router.callback_query(
    AdminPanelStates.confirmations,
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


@router.callback_query(
    AdminPanelStates.confirmations,
    F.data == "admin_confirm"
)
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment = data["payments"][data["index"]]

    async for session in get_session():
        await PaymentDAO.confirm_payment(
            session,
            payment.id,
            admin_id=callback.from_user.id
        )

    await callback.answer("✅ Платёж подтверждён")
    await open_confirmations(callback, state)


@router.callback_query(
    AdminPanelStates.confirmations,
    F.data == "admin_reject"
)
async def reject_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment = data["payments"][data["index"]]

    async for session in get_session():
        await PaymentDAO.reject_payment(
            session,
            payment.id,
            admin_id=callback.from_user.id
        )

    await callback.answer("❌ Платёж отклонён")
    await open_confirmations(callback, state)


@router.callback_query(F.data == "admin_back")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🛠️ <b>Админ-панель VPN Bot</b>\n\nВыберите раздел:",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()
