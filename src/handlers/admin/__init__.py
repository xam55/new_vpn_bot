from aiogram import Router

# ЕДИНЫЙ роутер для всей админки
admin_router = Router()

# Просто импортируем файлы,
# они НАВЕШИВАЮТ handlers на admin_router
from . import panel  # noqa
from . import keys   # noqa
from . import users  # noqa
