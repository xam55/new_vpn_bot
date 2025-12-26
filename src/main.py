import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import config
from src.bot.loader import setup_middlewares, setup_routers
from src.services.database import create_db_pool, close_db_pool
from src.services.scheduler import scheduler_service
from src.utils.logger import setup_logging

# Настраиваем логирование
logger = setup_logging()


async def main() -> None:
    """Главная функция запуска бота"""

    # Создаем бота
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Создаем диспетчер с MemoryStorage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Настраиваем middleware
    await setup_middlewares(dp)

    # Подключаем роутеры
    routers = setup_routers()
    for router in routers:
        dp.include_router(router)

    # Уведомляем админов о запуске
    await notify_admins(bot)

    # Запускаем планировщик для очистки просроченных ключей
    scheduler_service.start()
    logger.info("Планировщик запущен")

    # Запускаем бота
    logger.info("Бот запускается...")
    print("✅ Бот запущен! Ищите в Telegram")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler_service.stop()
        await bot.session.close()


async def notify_admins(bot: Bot) -> None:
    """Уведомление администраторов о запуске бота"""
    if not config.bot.admin_ids:
        return

    for admin_id in config.bot.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                "🤖 <b>VPN Bot запущен!</b>\n\n"
                "Бот успешно запущен и готов к работе.\n"
                "Статус: <code>🟢 Online</code>"
            )
            logger.info(f"Уведомление отправлено админу {admin_id}")
        except Exception as e:
            logger.error(f"Не удалось уведомить админа {admin_id}: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        exit(1)