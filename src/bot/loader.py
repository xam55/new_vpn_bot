from aiogram import Dispatcher
from src.bot.middlewares.throttling import ThrottlingMiddleware
from src.bot.middlewares.database import DatabaseMiddleware

from src.handlers.start import start_router
from src.handlers.admin import admin_router
from src.handlers.status import status_router

# Используем единый vpn_key_router из __init__.py папки vpn_key
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
        admin_router,
        start_router,
        vpn_key_router,
        status_router,
    ]
