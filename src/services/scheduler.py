"""
SCHEDULER.PY - Планировщик для автоматического удаления просроченных ключей
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from src.services.database import get_session
from src.services.vpn_service import VPNService
from src.utils.constants import VPNKeyStatus

logger = logging.getLogger(__name__)


class SchedulerService:
    """Планировщик для автоматической очистки просроченных ключей"""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def _cleanup_expired_keys(self):
        """Очистка просроченных ключей"""
        try:
            async for session in get_session():
                vpn_service = VPNService(session)
                expired_keys = await vpn_service.get_expired_keys()

                if not expired_keys:
                    logger.debug("Нет просроченных ключей для удаления")
                    return

                logger.info(f"Найдено {len(expired_keys)} просроченных ключей")

                for key in expired_keys:
                    try:
                        # Удаляем ключ с сервера
                        removed = await vpn_service.revoke_vpn_key(key.id)
                        if removed:
                            logger.info(f"Ключ {key.key_name} успешно удален")
                        else:
                            logger.warning(f"Не удалось удалить ключ {key.key_name}")
                    except Exception as e:
                        logger.error(f"Ошибка при удалении ключа {key.key_name}: {e}")

        except Exception as e:
            logger.error(f"Ошибка в планировщике очистки: {e}")

    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        logger.info("Планировщик запущен")
        while self._running:
            try:
                await self._cleanup_expired_keys()
                # Ждем 1 час перед следующей проверкой
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                logger.info("Планировщик остановлен")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле планировщика: {e}")
                await asyncio.sleep(60)  # Ждем минуту перед повтором при ошибке

    def start(self):
        """Запуск планировщика"""
        if self._running:
            logger.warning("Планировщик уже запущен")
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Планировщик запущен")

    def stop(self):
        """Остановка планировщика"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Планировщик остановлен")


# Создаем глобальный экземпляр
scheduler_service = SchedulerService()