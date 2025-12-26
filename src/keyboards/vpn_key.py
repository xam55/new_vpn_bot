from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_duration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора длительности ключа"""
    builder = InlineKeyboardBuilder()

    # Кнопки с популярными периодами (в днях)
    durations = [
        (1, "1 день - 10₽"),
        (7, "7 дней - 70₽"),
        (30, "30 дней - 300₽"),
        (90, "90 дней - 900₽"),
        (180, "180 дней - 1800₽"),
        (365, "365 дней - 3650₽")
    ]

    # Создаем кнопки в 2 колонки
    for i in range(0, len(durations), 2):
        row = durations[i:i + 2]
        for days, text in row:
            builder.button(text=text, callback_data=f"duration_{days}")
        builder.adjust(2)

    # Кнопка для ручного ввода
    builder.row(
        InlineKeyboardButton(text="✏️ Другое количество дней", callback_data="duration_custom")
    )

    # Кнопка отмены
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )

    return builder.as_markup()


def get_payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора способа оплаты"""
    builder = InlineKeyboardBuilder()

    payment_methods = [
        ("card", "💳 Банковская карта"),
        # Оставляем только банковскую карту
    ]

    # Создаем кнопки в 2 колонки
    for method, text in payment_methods:
        builder.button(text=text, callback_data=f"payment_{method}")

    builder.adjust(1)  # Теперь 1 колонка

    # Кнопки действий
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_duration"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )

    return builder.as_markup()


def get_payment_confirmation_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения оплаты"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_{payment_id}"),
        InlineKeyboardButton(text="📸 Отправить скриншот", callback_data=f"photo_{payment_id}")
    )

    builder.row(
        InlineKeyboardButton(text="❌ Отменить оплату", callback_data=f"cancel_payment_{payment_id}")
    )

    return builder.as_markup()


def get_user_keys_keyboard(keys: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком ключей пользователя"""
    builder = InlineKeyboardBuilder()

    if not keys:
        builder.button(text="🔑 Купить первый ключ", callback_data="buy_first_key")
    else:
        for key in keys:
            builder.button(
                text=f"🔑 {key.key_name} ({key.days_left} дн.)",
                callback_data=f"key_info_{key.id}"
            )
        builder.adjust(1)

    builder.row(
        InlineKeyboardButton(text="🔄 Обновить список", callback_data="refresh_keys"),
        InlineKeyboardButton(text="🔑 Купить ещё", callback_data="buy_more")
    )

    return builder.as_markup()


def get_key_actions_keyboard(key_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с действиями для ключа"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📥 Скачать конфиг", callback_data=f"download_{key_id}"),
        InlineKeyboardButton(text="📷 QR код", callback_data=f"qr_{key_id}")
    )

    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"renew_{key_id}"),
        InlineKeyboardButton(text="ℹ️ Инструкция", callback_data=f"instruction_{key_id}")
    )

    return builder.as_markup()