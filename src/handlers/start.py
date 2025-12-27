import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from src.keyboards.admin import get_admin_panel_keyboard
from src.keyboards import get_main_menu, get_admin_menu
from src.config import config
from src.services.dao import UserDAO
from src.services import get_session

start_router = Router()
router = start_router  # Alias паттерн


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    async for session in get_session():
        await UserDAO.get_or_create(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

    is_admin = message.from_user.id in config.bot.admin_ids

    welcome_text = (
    "🚀 <b>Добро пожаловать в VPN Bot!</b>\n\n"
    "🔐 Здесь ты можешь <b>быстро и безопасно</b> получить VPN-доступ "
    "для защиты данных и свободного интернета.\n\n"

    "✨ <b>Почему мы?</b>\n"
    "• 🌍 Высокая скорость и стабильность\n"
    "• 🛡 Полная конфиденциальность\n"
    "• 📱 Поддержка всех устройств\n\n"

    "💰 <b>Тарифы:</b>\n"
    "• 🗓 <b>30 дней</b> — 300 ₽\n"
    "• 🗓 <b>90 дней</b> — 800 ₽ (выгодно 🔥)\n"
    "• 🗓 <b>180 дней</b> — 1400 ₽\n\n"

    "👇 <b>Доступные команды:</b>\n"
    "/vpnkey — 🔑 Купить VPN-ключ\n"
    "/mystatus — 📦 Мои ключи\n"
    "/help — ❓ Помощь\n\n"

    "🟢 <i>Статус сервиса: Online</i>"
)

    if is_admin:
        await message.answer(welcome_text, reply_markup=get_admin_menu())
    else:
        await message.answer(welcome_text, reply_markup=get_main_menu())


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    help_text = (
        "📚 <b>Помощь по использованию VPN Bot</b>\n\n"
        "### Как купить VPN:\n"
        "1. Нажмите /vpnkey\n"
        "2. Выберите срок действия\n"
        "3. Получите реквизиты для оплаты\n"
        "4. Отправьте скриншот оплаты\n"
        "5. Получите VPN конфиг\n\n"
        "### Как использовать VPN:\n"
        "1. Установите WireGuard с официального сайта\n"
        "2. Импортируйте полученный конфиг\n"
        "3. Активируйте подключение\n\n"
        "### Важная информация:\n"
        "- Ключ действует ровно указанное количество дней\n"
        "- Один ключ работает на всех ваших устройствах\n"
        "- Техподдержка: @ваш_ник_админа"
    )
    await message.answer(help_text)


@router.message(F.text == "💰 Цены")
async def show_prices(message: Message):
    prices_text = (
        "🏷️ <b>Тарифы VPN Bot</b>\n\n"
        "- 1 день — 10₽\n"
        "- 30 дней — 300₽\n"
        "- 365 дней — 3650₽\n\n"
        "Для покупки нажмите /vpnkey или выберите кнопку в меню."
    )
    await message.answer(prices_text)



logger = logging.getLogger(__name__)


@router.message(F.text == "👑 Админ-панель")
async def open_admin_panel_from_menu(message: Message, state: FSMContext):
    if message.from_user.id not in config.bot.admin_ids:
        await message.answer("❌ У вас нет прав администратора")
        return

    await state.clear()

    await message.answer(
        "🛠️ <b>Админ-панель VPN Bot</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=get_admin_panel_keyboard()
    )
