
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для возврата назад"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="⬅️ Назад"))
    return builder.as_markup(resize_keyboard=True)


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню для пользователей"""
    builder = ReplyKeyboardBuilder()

    builder.row(KeyboardButton(text="🔑 Купить VPN ключ"))
    builder.row(
        KeyboardButton(text="💰 Цены"),
        KeyboardButton(text="ℹ️ Помощь")
    )

    return builder.as_markup(resize_keyboard=True)


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Меню для администраторов"""
    builder = ReplyKeyboardBuilder()

    builder.row(KeyboardButton(text="👑 Админ-панель"))
    builder.row(KeyboardButton(text="🔑 Купить VPN ключ"))
    builder.row(
        KeyboardButton(text="💰 Цены"),
        KeyboardButton(text="ℹ️ Помощь")
    )

    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отмены"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)