import asyncio
from src.services.database import create_db_pool, get_session
from src.services.dao import UserDAO


async def make_admin(telegram_id: int):
    await create_db_pool()

    async for session in get_session():
        user = await UserDAO.get_by_telegram_id(session, telegram_id)
        if user:
            user.is_admin = True
            await session.commit()
            print(f"✅ Пользователь {telegram_id} теперь админ")
        else:
            print(f"❌ Пользователь {telegram_id} не найден в базе")


if __name__ == "__main__":
    # Укажи свой Telegram ID
    asyncio.run(make_admin(7672667340))