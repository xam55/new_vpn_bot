from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncEngine
from typing import AsyncGenerator

from src.config import config

# Движок базы данных
engine: AsyncEngine | None = None
async_session_maker: async_sessionmaker[AsyncSession] | None = None


async def create_db_pool() -> None:
    """Создание пула соединений с базой данных"""
    global engine, async_session_maker


    # Создаем асинхронный движок
    engine_kwargs = {
        'echo': False,
        'pool_pre_ping': True
    }
    if config.db.url.startswith('postgresql'):
        engine_kwargs['pool_size'] = 20
        engine_kwargs['max_overflow'] = 10

    engine = create_async_engine(
        config.db.url,
        **engine_kwargs
    )

    # Создаем фабрику сессий
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Импортируем Base ПОСЛЕ создания движка
    from src.models.base import Base

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db_pool() -> None:
    """Закрытие пула соединений"""
    if engine:
        await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Генератор сессий"""
    if not async_session_maker:
        raise RuntimeError("База данных не инициализирована")

    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()