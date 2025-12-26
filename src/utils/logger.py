import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging():
    """Настройка системы логирования"""

    # Создаем папку для логов
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Настраиваем логгер
    logger = logging.getLogger("vpn_bot")
    logger.setLevel(logging.INFO)

    # Форматтер
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Консольный хендлер
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Файловый хендлер
    file_handler = RotatingFileHandler(
        filename=log_dir / "vpn_bot.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Добавляем хендлеры
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Отключаем логи для некоторых библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)

    return logger