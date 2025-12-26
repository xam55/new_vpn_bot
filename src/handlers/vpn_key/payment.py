from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from src.states.vpn_states import VPNPurchaseStates
from src.services import get_session, PaymentDAO, UserDAO
from src.config import config

payment_router = Router()
router = payment_router


@router.message(
    VPNPurchaseStates.waiting_payment_proof,
    F.photo | F.document
)
async def process_payment_proof(message: Message, state: FSMContext):
    """Обработка скриншота оплаты от пользователя"""
    data = await state.get_data()
    payment_code = data.get("payment_id")

    if not payment_code:
        await message.answer("❌ Платёж не найден. Начните заново /vpnkey")
        return

    file_id = (
        message.photo[-1].file_id
        if message.photo
        else message.document.file_id
    )

    async for session in get_session():
        payment = await PaymentDAO.get_by_payment_id(session, payment_code)

        if not payment:
            await message.answer("❌ Платёж не найден в базе")
            return

        await PaymentDAO.mark_as_paid(
            session=session,
            payment_id=payment.id,
            proof_photo_id=file_id
        )

        admins = await UserDAO.get_admins(session)

        for admin in admins:
            await message.bot.send_photo(
                admin.telegram_id,
                photo=file_id,
                caption=(
                    "💰 <b>Новый платёж</b>\n\n"
                    f"👤 Пользователь: {message.from_user.full_name}\n"
                    f"🆔 TG ID: {message.from_user.id}\n"
                    f"💳 Payment ID: <code>{payment.payment_id}</code>\n"
                    f"💰 Сумма: {payment.amount}₽"
                ),
                parse_mode="HTML"
            )

    await message.answer(
        "✅ <b>Чек получен!</b>\n\n"
        "Платёж отправлен администратору на проверку.\n"
        "Ожидайте подтверждения ⏳",
        parse_mode="HTML"
    )

    await state.clear()


@router.callback_query(F.data.startswith("paid_"))
async def process_paid_without_photo(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия 'Я оплатил' без скриншота"""
    data = await state.get_data()
    payment_code = data.get("payment_id")

    if not payment_code:
        await callback.answer("❌ Платёж не найден. Начните заново /vpnkey", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer(
        "⚠️ <b>Пожалуйста, отправьте скриншот чека об оплате</b>\n\n"
        "Для подтверждения оплаты необходимо отправить скриншот.\n"
        "Просто отправьте фото или документ с чеком.",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("photo_"))
async def request_payment_proof(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия 'Отправить скриншот'"""
    await callback.answer()
    await callback.message.answer(
        "📸 <b>Отправьте скриншот чека об оплате</b>\n\n"
        "Просто отправьте фото или документ с подтверждением оплаты.",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_payment_process(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса оплаты"""
    try:
        payment_string_id = callback.data.split("_", 1)[1]

        async for session in get_session():
            # Находим платеж
            payment = await PaymentDAO.get_by_payment_id(session, payment_string_id)
            if payment:
                # ✅ ИСПРАВЛЕНО: используем новый метод cancel_payment
                await PaymentDAO.cancel_payment(session, payment.id)

    except Exception as e:
        print(f"Ошибка при отмене платежа: {e}")

    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Оплата отменена</b>\n\n"
        "Вы можете начать заново с помощью команды /vpnkey"
    )
    await callback.answer("Оплата отменена")


@router.callback_query(F.data.startswith("confirm_payment_"))
async def admin_confirm_payment(callback: CallbackQuery):
    """Админ подтверждает платёж"""
    try:
        payment_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка получения ID платежа", show_alert=True)
        return

    async for session in get_session():
        payment = await PaymentDAO.get_by_id(session, payment_id)
        if not payment:
            await callback.answer("❌ Платёж не найден", show_alert=True)
            return

        # ✅ ИСПРАВЛЕНО: передаем admin_id и comment
        await PaymentDAO.confirm_payment(
            session,
            payment_id,
            admin_id=callback.from_user.id,
            comment="Платеж подтвержден администратором"
        )

        # Уведомить пользователя
        await callback.bot.send_message(
            payment.user.telegram_id,
            "✅ <b>Ваш платёж подтверждён!</b>\n\n"
            "Создаю VPN ключ... ⏳",
            parse_mode="HTML"
        )

    await callback.message.edit_text(
        f"✅ Платёж #{payment_id} подтверждён. Ключ создаётся для пользователя."
    )
    await callback.answer("Платёж подтверждён")


@router.callback_query(F.data.startswith("reject_payment_"))
async def admin_reject_payment(callback: CallbackQuery):
    """Админ отклоняет платёж"""
    try:
        payment_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка получения ID платежа", show_alert=True)
        return

    async for session in get_session():
        payment = await PaymentDAO.get_by_id(session, payment_id)
        if not payment:
            await callback.answer("❌ Платёж не найден", show_alert=True)
            return

        # ✅ ИСПРАВЛЕНО: передаем admin_id и comment
        await PaymentDAO.reject_payment(
            session,
            payment_id,
            admin_id=callback.from_user.id,
            comment="Платеж отклонен администратором"
        )

        # Уведомить пользователя
        await callback.bot.send_message(
            payment.user.telegram_id,
            "❌ <b>Ваш платёж отклонён</b>\n\n"
            "Возможные причины:\n"
            "- Неправильный комментарий\n"
            "- Сумма не совпадает\n"
            "- Скриншот нечитаем\n\n"
            "Вы можете попробовать снова: /vpnkey",
            parse_mode="HTML"
        )

    await callback.message.edit_text(
        f"❌ Платёж #{payment_id} отклонён. Пользователь уведомлён."
    )
    await callback.answer("Платёж отклонён")