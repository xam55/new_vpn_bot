#!/usr/bin/env python3
"""
ЗАПУСК VPN БОТА
"""

import asyncio
import sys
import os
import logging

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Добавляем src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


async def main():
    """Основная функция запуска"""

    print("=" * 50)
    print("🤖 VPN БОТ - ЗАПУСК")
    print("=" * 50)

    # Проверяем .env
    if not os.path.exists(".env"):
        logger.error("Файл .env не найден!")
        print("❌ Создайте файл .env на основе .env.example")
        return

    from src.config import config
    from src.services.database import create_db_pool, close_db_pool

    print("1. Проверка конфигурации...")
    if not config.bot.token or config.bot.token == "ВАШ_ТОКЕН_ОТ_BOTFATHER":
        logger.error("BOT_TOKEN не установлен")
        print("❌ Установите BOT_TOKEN в .env файле")
        return

    print(f"   ✅ Токен: {config.bot.token[:15]}...")
    print(f"   ✅ Админы: {config.bot.admin_ids}")

    print("2. Создание папок...")
    os.makedirs("data/database", exist_ok=True)
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs("data/backups", exist_ok=True)

    print("3. Инициализация базы данных...")
    try:
        await create_db_pool()
        logger.info("База данных создана")
        print("   ✅ База данных создана")
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        print(f"   ❌ Ошибка: {e}")
        return

    print("4. Запуск бота...")
    print("   Нажмите Ctrl+C для остановки")
    print("=" * 50)

    try:
        from src.main import main as bot_main
        await bot_main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
        print("\n🛑 Бот остановлен")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n💥 Критическая ошибка: {e}")
    finally:
        print("\n🧹 Очистка ресурсов...")
        await close_db_pool()
        print("👋 Завершено")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Принудительная остановка")