from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from src.services.database import async_session_maker


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для работы с базой данных"""

    async def __call__(
            self,
            handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
            event: Any,
            data: Dict[str, Any]
    ) -> Any:
        async with async_session_maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise e