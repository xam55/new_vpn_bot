import sys
import os

sys.path.append('src')

# Проверяем основные импорты
try:
    from src.models.base import Base

    print("✅ Base импортирован")

    from src.config import config

    print(f"✅ Конфиг загружен. Токен: {config.bot.token[:15]}...")

    from src.services.database import create_db_pool, close_db_pool

    print("✅ Database функции импортированы")

    import asyncio


    async def test():
        await create_db_pool()
        print("✅ База данных создана")
        await close_db_pool()


    asyncio.run(test())
    print("✅ ВСЕ ОК! Бот должен запускаться")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback

    traceback.print_exc()
