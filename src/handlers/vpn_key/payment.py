from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.context import FSMContext
import logging
import asyncio

from src.states.vpn_states import VPNPurchaseStates
from src.services import get_session, PaymentDAO, UserDAO
from src.config import config

payment_router = Router()
router = payment_router
logger = logging.getLogger(__name__)


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

    logger.info(f"📸 Получен чек оплаты: file_id={file_id}, payment_code={payment_code}")

    async for session in get_session():
        payment = await PaymentDAO.get_by_payment_id(session, payment_code)

        if not payment:
            await message.answer("❌ Платёж не найден в базе")
            logger.error(f"❌ Платёж {payment_code} не найден в БД")
            return

        # Обновляем статус платежа
        await PaymentDAO.mark_as_paid(
            session=session,
            payment_id=payment.id,
            proof_photo_id=file_id
        )

        # Получаем администраторов из базы
        admins = await UserDAO.get_admins(session)

        if not admins:
            # Если нет админов в базе, используем ID из конфига
            admin_ids = getattr(config.bot, 'admin_ids', [])
            logger.warning(f"⚠️ Админы не найдены в БД, используем конфиг: {admin_ids}")

            if not admin_ids:
                logger.error("❌ Нет администраторов для уведомления!")
                await message.answer(
                    "✅ <b>Чек получен, но администратор не найден!</b>\n\n"
                    "Пожалуйста, сообщите администратору вручную.",
                    parse_mode="HTML"
                )
                return

            # Отправляем админам из конфига
            for admin_id in admin_ids:
                try:
                    logger.info(f"📤 Отправка чека админу {admin_id}...")
                    await message.bot.send_photo(
                        chat_id=admin_id,
                        photo=file_id,
                        caption=(
                            "💰 <b>НОВЫЙ ПЛАТЁЖ НА ПРОВЕРКУ</b>\n\n"
                            f"👤 Пользователь: {message.from_user.full_name}\n"
                            f"🆔 TG ID: {message.from_user.id}\n"
                            f"📱 Username: @{message.from_user.username}\n"
                            f"💳 Payment ID: <code>{payment.payment_id}</code>\n"
                            f"💰 Сумма: {payment.amount}₽\n"
                            f"📅 Дата: {payment.created_at.strftime('%d.%m.%Y %H:%M') if payment.created_at else 'N/A'}\n\n"
                            "⚡ <i>Для подтверждения используйте админ-панель</i>"
                        ),
                        parse_mode="HTML"
                    )
                    logger.info(f"✅ Чек отправлен админу {admin_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки админу {admin_id}: {str(e)}")

        else:
            # Отправляем админам из базы
            for admin in admins:
                try:
                    logger.info(f"📤 Отправка чека админу {admin.telegram_id} ({admin.username})...")
                    await message.bot.send_photo(
                        chat_id=admin.telegram_id,
                        photo=file_id,
                        caption=(
                            "💰 <b>НОВЫЙ ПЛАТЁЖ НА ПРОВЕРКУ</b>\n\n"
                            f"👤 Пользователь: {message.from_user.full_name}\n"
                            f"🆔 TG ID: {message.from_user.id}\n"
                            f"📱 Username: @{message.from_user.username}\n"
                            f"💳 Payment ID: <code>{payment.payment_id}</code>\n"
                            f"💰 Сумма: {payment.amount}₽\n"
                            f"📅 Дата: {payment.created_at.strftime('%d.%m.%Y %H:%M') if payment.created_at else 'N/A'}\n\n"
                            "⚡ <i>Для подтверждения используйте админ-панель</i>"
                        ),
                        parse_mode="HTML"
                    )
                    logger.info(f"✅ Чек отправлен админу {admin.telegram_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки админу {admin.telegram_id}: {str(e)}")

    await message.answer(
        "✅ <b>Чек получен!</b>\n\n"
        "Платёж отправлен администратору на проверку.\n"
        "Ожидайте подтверждения ⏳",
        parse_mode="HTML"
    )

    await state.clear()
    logger.info("✅ Процесс оплаты завершен, состояние очищено")


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
        logger.error(f"Ошибка при отмене платежа: {e}")

    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Оплата отменена</b>\n\n"
        "Вы можете начать заново с помощью команды /vpnkey"
    )
    await callback.answer("Оплата отменена")

