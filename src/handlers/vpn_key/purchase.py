from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.states.vpn_states import VPNPurchaseStates
from src.keyboards import (
    get_duration_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
    get_payment_methods_keyboard
)
from src.utils.validators import validate_days_input
from src.utils.constants import MIN_KEY_DURATION_DAYS, MAX_KEY_DURATION_DAYS

from src.config import config
from src.services import get_session, UserDAO

purchase_router = Router()
router = purchase_router  # Alias паттерн


@router.message(Command("vpnkey"))
@router.message(F.text == "🔑 Купить VPN ключ")
async def cmd_vpn_key(message: Message, state: FSMContext):
    """Начало покупки VPN ключа"""

    # Очищаем предыдущее состояние
    await state.clear()

    # Проверяем, не заблокирован ли пользователь
    async for session in get_session():
        user = await UserDAO.get_by_telegram_id(session, message.from_user.id)
        if user and user.is_banned:
            await message.answer(
                "🚫 <b>Ваш аккаунт заблокирован!</b>\n\n"
                "Вы не можете приобретать VPN ключи.\n"
                "Для выяснения причин обратитесь к администратору."
            )
            return

    # Устанавливаем состояние выбора длительности
    await state.set_state(VPNPurchaseStates.select_duration)

    # Отправляем сообщение с выбором длительности
    await message.answer(
        "⏳ <b>Выберите срок действия VPN ключа</b>\n\n"
        "Сколько дней должен действовать ваш VPN ключ?\n\n"
        "<i>Цена: 10₽ за 1 день использования</i>",
        reply_markup=get_duration_keyboard()
    )


@router.callback_query(F.data.startswith("duration_"))
async def process_duration_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора длительности ключа"""

    data = callback.data

    if data == "duration_custom":
        # Пользователь хочет ввести свой срок
        await callback.message.edit_text(
            "✏️ <b>Введите количество дней</b>\n\n"
            f"От {MIN_KEY_DURATION_DAYS} до {MAX_KEY_DURATION_DAYS} дней.\n\n"
            "<i>Цена рассчитывается как: дни × 10₽</i>",
            reply_markup=get_back_keyboard()
        )

        await state.set_state(VPNPurchaseStates.custom_duration)
        await callback.answer()
        return

    # Извлекаем количество дней из callback_data
    try:
        days = int(data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка выбора длительности", show_alert=True)
        return

    # Проверяем валидность
    if not MIN_KEY_DURATION_DAYS <= days <= MAX_KEY_DURATION_DAYS:
        await callback.answer(f"❌ Срок должен быть от {MIN_KEY_DURATION_DAYS} до {MAX_KEY_DURATION_DAYS} дней",
                              show_alert=True)
        return

    # Сохраняем данные в состоянии
    await state.update_data(days=days)

    # Переходим к выбору способа оплаты
    await callback.message.edit_text(
        f"✅ <b>Выбрано: {days} дней</b>\n\n"
        f"💰 Стоимость: <b>{days * config.payment.price_per_day}₽</b>\n\n"
        "💳 <b>Выберите способ оплаты:</b>",
        reply_markup=get_payment_methods_keyboard()
    )

    await state.set_state(VPNPurchaseStates.select_payment_method)
    await callback.answer()


@router.message(VPNPurchaseStates.custom_duration)
async def process_custom_duration(message: Message, state: FSMContext):
    """Обработка ввода пользовательской длительности"""

    # Проверяем, не отмена ли
    if message.text == "↩️ Назад":
        await message.answer(
            "⏳ <b>Выберите срок действия VPN ключа</b>\n\n"
            "Сколько дней должен действовать ваш VPN ключ?\n\n"
            "<i>Цена: 10₽ за 1 день использования</i>",
            reply_markup=get_duration_keyboard()
        )
        await state.set_state(VPNPurchaseStates.select_duration)
        return

    # Проверяем валидность ввода
    days = validate_days_input(
        message.text,
        min_days=MIN_KEY_DURATION_DAYS,
        max_days=MAX_KEY_DURATION_DAYS
    )

    if days is None:
        await message.answer(
            f"❌ <b>Некорректный ввод!</b>\n\n"
            f"Введите число от {MIN_KEY_DURATION_DAYS} до {MAX_KEY_DURATION_DAYS}.\n\n"
            "<i>Пример: 30 (для 30 дней)</i>",
            reply_markup=get_back_keyboard()
        )
        return

    # Сохраняем данные в состоянии
    await state.update_data(days=days)

    # Переходим к выбору способа оплаты
    await message.answer(
        f"✅ <b>Выбрано: {days} дней</b>\n\n"
        f"💰 Стоимость: <b>{days * config.payment.price_per_day}₽</b>\n\n"
        "💳 <b>Выберите способ оплаты:</b>",
        reply_markup=get_payment_methods_keyboard()
    )

    await state.set_state(VPNPurchaseStates.select_payment_method)


@router.callback_query(F.data.startswith("payment_"))
async def process_payment_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора способа оплаты"""
    payment_method = callback.data.split("_")[1]

    # Получаем данные о выбранной длительности
    data = await state.get_data()
    days = data.get("days")

    if not days:
        await callback.answer("❌ Ошибка: не выбрана длительность", show_alert=True)
        return

    # Рассчитываем стоимость
    amount = days * 10  # 10₽ в день

    # Сохраняем метод оплаты
    await state.update_data(payment_method=payment_method, amount=amount)

    # Генерируем ID платежа
    from datetime import datetime
    import random
    payment_id = f"PAY-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

    await state.update_data(payment_id=payment_id)

    # Показываем реквизиты для оплаты
    payment_text = (
        "### Реквизиты для оплаты\n\n"
        f"ID платежа: {payment_id}\n"
        f"Сумма: {amount}₽\n"
        "Комментарий: VPN-BOT\n\n"
        "Банк: Тинькофф\n"
        "Номер карты: 5536 9138 1234 5678\n"
        "Получатель: ИВАНОВ ИВАН\n\n"
        "### Внимание!\n"
        "- Обязательно укажите комментарий к платежу\n"
        "- После оплаты отправьте скриншот чека\n"
        "- Обычно подтверждение занимает до 15 минут"
    )

    await callback.message.edit_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_{payment_id}"),
            InlineKeyboardButton(text="📸 Отправить скриншот", callback_data=f"photo_{payment_id}")
        ], [
            InlineKeyboardButton(text="❌ Отменить оплату", callback_data="cancel_payment")
        ]])
    )

    # Переходим в состояние ожидания подтверждения оплаты
    await state.set_state(VPNPurchaseStates.waiting_payment_proof)
    await callback.answer()


@router.callback_query(F.data == "back_to_duration")
async def back_to_duration(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору длительности"""
    await callback.message.edit_text(
        "⏳ <b>Выберите срок действия VPN ключа</b>\n\n"
        "Сколько дней должен действовать ваш VPN ключ?\n\n"
        "<i>Цена: 10₽ за 1 день использования</i>",
        reply_markup=get_duration_keyboard()
    )

    await state.set_state(VPNPurchaseStates.select_duration)
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
    """Отмена покупки"""
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Покупка VPN ключа отменена</b>\n\n"
        "Вы можете начать заново с помощью команды /vpnkey"
    )

    await callback.answer("Покупка отменена")