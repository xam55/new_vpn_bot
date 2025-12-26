from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_payment_actions_keyboard(payment_id: int):
    """Клавиатура для подтверждения или отклонения платежа админом"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_payment_{payment_id}"),
        InlineKeyboardButton(text="↩️ Отклонить", callback_data=f"reject_payment_{payment_id}")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
    )
    return builder.as_markup()


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✅ Подтверждения", callback_data="admin_confirmations"),
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
    )

    builder.row(
        InlineKeyboardButton(text="🔑 Все ключи", callback_data="admin_keys"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )

    builder.row(
        InlineKeyboardButton(text="⬅️ В главное меню", callback_data="admin_back_to_main")
    )

    return builder.as_markup()


def get_duration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора длительности"""
    builder = InlineKeyboardBuilder()

    durations = [
        (1, "1 день - 10₽"),
        (7, "7 дней - 70₽"),
        (30, "30 дней - 300₽"),
        (90, "90 дней - 900₽"),
        (180, "180 дней - 1800₽"),
        (365, "365 дней - 3650₽")
    ]

    for days, text in durations:
        builder.button(text=text, callback_data=f"duration_{days}")

    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )

    return builder.as_markup()


def get_payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора способа оплаты"""
    builder = InlineKeyboardBuilder()

    methods = [
        ("card", "💳 Банковская карта"),
        # Убраны QIWI и WebMoney
    ]

    for method, text in methods:
        builder.button(text=text, callback_data=f"payment_{method}")

    builder.adjust(1)  # Теперь 1 кнопка в ряду

    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_duration"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )

    return builder.as_markup()