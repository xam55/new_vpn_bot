from aiogram import Router

admin_router = Router()

from .panel import router as panel_router
from .keys import router as keys_router
from .users import router as users_router

admin_router.include_router(panel_router)
admin_router.include_router(keys_router)
admin_router.include_router(users_router)

__all__ = ["admin_router"]
