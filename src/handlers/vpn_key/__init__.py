from aiogram import Router
from .purchase import purchase_router
from .payment import payment_router
# from .confirm import confirm_router

vpn_key_router = Router()
vpn_key_router.include_router(purchase_router)
vpn_key_router.include_router(payment_router)
# vpn_key_router.include_router(confirm_router)

__all__ = ["vpn_key_router"]