from aiogram import Dispatcher
from src.bot.middlewares.throttling import ThrottlingMiddleware
from src.bot.middlewares.database import DatabaseMiddleware

from src.handlers.start import start_router
from src.handlers.admin import admin_router
from src.handlers.status import status_router

# Импортируем ЕДИНЫЙ роутер из vpn_key
from src.handlers.vpn_key import vpn_key_router


async def setup_middlewares(dp: Dispatcher) -> None:
    """
    Подключение middleware
    """
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(ThrottlingMiddleware())


def setup_routers() -> list:
    """
    Регистрация роутеров
    ВАЖНО: каждый роутер подключается ТОЛЬКО ОДИН РАЗ
    """
    return [
        start_router,
        vpn_key_router,  # Только один роутер вместо отдельных
        admin_router,
        status_router,
    ]