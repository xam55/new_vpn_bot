from aiogram import Router

# Импортируем роутеры админки
from .panel import router as panel_router
# Можно добавить другие: users_router, keys_router и т.д.

admin_router = Router()
admin_router.include_router(panel_router)

__all__ = ["admin_router"]
