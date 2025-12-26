from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_yes_no_keyboard(yes_data: str = "yes", no_data: str = "no") -> InlineKeyboardMarkup:
    """Универсальная клавиатура Да/Нет"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=yes_data),
        InlineKeyboardButton(text="❌ Нет", callback_data=no_data)
    )

    return builder.as_markup()


def get_numeric_keyboard(max_num: int = 365, cols: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура с цифрами для выбора количества дней"""
    builder = InlineKeyboardBuilder()

    # Создаем кнопки с цифрами
    for i in range(1, max_num + 1):
        if i <= 30 or i % 30 == 0 or i == 365:
            builder.button(text=str(i), callback_data=f"num_{i}")

    builder.adjust(cols)

    # Дополнительные кнопки
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )

    return builder.as_markup()


def get_close_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой закрыть"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="❌ Закрыть", callback_data="close")
    )

    return builder.as_markup()


def get_support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для связи с поддержкой"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="💬 Написать в поддержку", url="https://t.me/username")
    )

    builder.row(
        InlineKeyboardButton(text="📞 Связаться с админом", url="https://t.me/admin_username")
    )

    return builder.as_markup()