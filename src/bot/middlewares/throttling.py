from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from cachetools import TTLCache
import time


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для защиты от спама"""

    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.cache = TTLCache(maxsize=10000, ttl=3600)

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return await handler(event, data)

        last_time = self.cache.get(user_id)
        current_time = time.time()

        if last_time and (current_time - last_time) < self.rate_limit:
            if isinstance(event, Message) and (current_time - last_time) > 0.1:
                await event.answer("⏳ Слишком много запросов! Подождите немного.")
            return

        self.cache[user_id] = current_time
        return await handler(event, data)