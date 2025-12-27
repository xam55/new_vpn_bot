import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import config
from src.bot.loader import setup_middlewares, setup_routers
from src.services.database import create_db_pool, close_db_pool
from src.utils.logger import setup_logging

logger = setup_logging()


async def main() -> None:
    """Главная функция запуска бота"""

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # middleware
    await setup_middlewares(dp)

    # routers
    for router in setup_routers():
        dp.include_router(router)

    # уведомляем админов
    await notify_admins(bot)

    logger.info("🤖 Бот запущен и принимает апдейты")

    try:
        # 🔥 ВОТ ЧЕГО НЕ ХВАТАЛО
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def notify_admins(bot: Bot) -> None:
    if not config.bot.admin_ids:
        return

    for admin_id in config.bot.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                "🤖 <b>VPN Bot запущен!</b>\n\n"
                "Статус: <code>🟢 Online</code>"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить админа {admin_id}: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
