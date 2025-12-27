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
from src.services.vpn_service import VPNService
from src.utils.constants import PRICE_PER_DAY
from src.models.payment import Payment

router = admin_router


# ===================== HELPERS =====================

def render_payment(payment: Payment, index: int, total: int) -> str:
    user = payment.user
    username = f"@{user.username}" if user.username else "без username"

    return (
        "💰 <b>Платёж на подтверждение</b>\n\n"
        f"👤 Пользователь: {user.full_name} ({username})\n"
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
        "👑 <b>Админ-панель</b>",
        reply_markup=get_admin_panel_keyboard()
    )


# ===================== CONFIRMATIONS =====================

@router.callback_query(F.data == "admin_confirmations")
async def open_confirmations(callback: CallbackQuery, state: FSMContext):
    async for session in get_session():
        result = await session.execute(
            select(Payment)
            .where(Payment.status == "paid")
            .options(selectinload(Payment.user))
            .order_by(Payment.created_at)
        )
        payments = result.scalars().all()

        payment_ids = [p.id for p in payments]

    if not payment_ids:
        await callback.answer("📭 Нет ожидающих платежей", show_alert=True)
        return

    await state.set_state(AdminPanelStates.confirmations_list)
    await state.update_data(payment_ids=payment_ids, index=0)

    await callback.message.edit_text(
        render_payment(payments[0], 0, len(payment_ids)),
        reply_markup=get_admin_confirmation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.in_(["admin_next", "admin_prev"]))
async def navigate_payments(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment_ids = data["payment_ids"]
    index = data["index"]

    if callback.data == "admin_next" and index < len(payment_ids) - 1:
        index += 1
    elif callback.data == "admin_prev" and index > 0:
        index -= 1

    async for session in get_session():
        payment = await PaymentDAO.get_by_id(session, payment_ids[index])
        await session.refresh(payment, ["user"])

    await state.update_data(index=index)

    await callback.message.edit_text(
        render_payment(payment, index, len(payment_ids)),
        reply_markup=get_admin_confirmation_keyboard()
    )
    await callback.answer()


# ===================== CONFIRM =====================

@router.callback_query(F.data == "admin_confirm")
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment_ids = data["payment_ids"]
    index = data["index"]

    async for session in get_session():
        payment = await PaymentDAO.get_by_id(session, payment_ids[index])
        user = payment.user

        await PaymentDAO.confirm_payment(
            session=session,
            payment_id=payment.id,
            admin_id=callback.from_user.id
        )

        days = int(payment.amount / PRICE_PER_DAY)
        vpn_service = VPNService(session)
        vpn_key = await vpn_service.create_vpn_key(user, days, payment)

    await callback.bot.send_message(
        user.telegram_id,
        (
            "🎉 <b>Платёж подтверждён!</b>\n\n"
            f"🔑 <code>{vpn_key.key_name}</code>\n\n"
            f"<pre>{vpn_key.config_data}</pre>\n\n"
            "🔗 https://www.wireguard.com/install/"
        )
    )

    payment_ids.pop(index)

    if not payment_ids:
        await state.clear()
        await callback.message.edit_text("✅ Все платежи обработаны")
        return

    await state.update_data(
        payment_ids=payment_ids,
        index=min(index, len(payment_ids) - 1)
    )

    await callback.answer("✅ Подтверждено")


# ===================== REJECT =====================

@router.callback_query(F.data == "admin_reject")
async def reject_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment_ids = data["payment_ids"]
    index = data["index"]

    async for session in get_session():
        payment = await PaymentDAO.get_by_id(session, payment_ids[index])
        user = payment.user

        await PaymentDAO.reject_payment(
            session=session,
            payment_id=payment.id,
            admin_id=callback.from_user.id
        )

    await callback.bot.send_message(
        user.telegram_id,
        "❌ <b>Платёж отклонён</b>\n\n"
        "Вы можете оплатить заново или связаться с поддержкой."
    )

    payment_ids.pop(index)

    if not payment_ids:
        await state.clear()
        await callback.message.edit_text("📭 Нет ожидающих платежей")
        return

    await state.update_data(
        payment_ids=payment_ids,
        index=min(index, len(payment_ids) - 1)
    )

    await callback.answer("❌ Отклонено")
