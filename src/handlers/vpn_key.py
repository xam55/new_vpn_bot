from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.keyboards import (
    get_duration_keyboard,
    get_payment_methods_keyboard,
    get_cancel_keyboard
)
from src.services.dao import UserDAO, PaymentDAO
from src.config import config
import json

router = Router()


class VPNPurchaseStates(StatesGroup):
    select_duration = State()
    select_payment = State()


@router.message(Command("vpnkey"))
@router.message(F.text == "🔑 Купить VPN ключ")
async def cmd_vpn_key(message: Message, state: FSMContext):
    """Начало покупки VPN ключа"""
    await state.clear()

    await message.answer(
        "⏳ <b>Выберите срок действия VPN ключа</b>\n\n"
        "Сколько дней должен действовать ваш VPN ключ?\n\n"
        "<i>Цена: 10₽ за 1 день использования</i>",
        reply_markup=get_duration_keyboard()
    )

    await state.set_state(VPNPurchaseStates.select_duration)


@router.callback_query(F.data.startswith("duration_"))
async def process_duration(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора длительности"""
    try:
        days = int(callback.data.split("_")[1])

        if days < 1 or days > 365:
            await callback.answer("❌ Выберите от 1 до 365 дней", show_alert=True)
            return

        amount = days * config.payment.price_per_day

        await state.update_data(days=days, amount=amount)

        await callback.message.edit_text(
            f"✅ <b>Выбрано: {days} дней</b>\n\n"
            f"💰 Стоимость: <b>{amount}₽</b>\n\n"
            "💳 <b>Выберите способ оплаты:</b>",
            reply_markup=get_payment_methods_keyboard()
        )

        await state.set_state(VPNPurchaseStates.select_payment)
        await callback.answer()

    except Exception as e:
        await callback.answer("❌ Ошибка выбора", show_alert=True)


@router.callback_query(F.data.startswith("payment_"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора способа оплаты"""
    data = await state.get_data()
    days = data.get('days')
    amount = data.get('amount')

    if not days or not amount:
        await callback.answer("❌ Ошибка: данные не найдены", show_alert=True)
        return

    method = callback.data.split("_")[1]

    # Генерируем реквизиты
    payment_details = {
        "method": method,
        "amount": amount,
        "days": days,
        "comment": f"VPN-{callback.from_user.id}"
    }

    if method == "card":
        payment_details.update({
            "bank": "Тинькофф",
            "card_number": "5536 9138 4697 5498",
            "cardholder": "ИВАН ИВАНОВ"
        })
    elif method == "qiwi":
        payment_details.update({
            "wallet": "+79001234567"
        })

    # Сохраняем платеж
    async for session in get_session():
        user = await UserDAO.get_by_telegram_id(session, callback.from_user.id)
        if user:
            payment_id = f"PAY-{callback.from_user.id}-{callback.message.message_id}"
            await PaymentDAO.create(
                session=session,
                user_id=user.id,
                payment_id=payment_id,
                amount=amount,
                method=method,
                payment_details=json.dumps(payment_details)
            )

    # Формируем сообщение
    message_text = f"""
💳 <b>Реквизиты для оплаты</b>

🆔 ID платежа: <code>{payment_id}</code>
💰 Сумма: <b>{amount}₽</b>
⏳ Срок: {days} дней
📝 Комментарий: <code>VPN-{callback.from_user.id}</code>

"""

    if method == "card":
        message_text += f"""
🏦 Банк: {payment_details['bank']}
💳 Номер карты: <code>{payment_details['card_number']}</code>
👤 Получатель: {payment_details['cardholder']}
"""
    elif method == "qiwi":
        message_text += f"""
🥝 QIWI кошелек: <code>{payment_details['wallet']}</code>
"""

    message_text += """
⚠️ <b>Внимание!</b>
• Обязательно укажите комментарий к платежу
• После оплаты отправьте скриншот чека
• Ожидайте подтверждения администратора
"""

    await callback.message.edit_text(
        message_text,
        reply_markup=get_cancel_keyboard()
    )

    await state.clear()
    await callback.answer("Реквизиты отправлены")