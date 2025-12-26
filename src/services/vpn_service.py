from typing import Dict, Any, Optional
import secrets
import string
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from src.models.user import User
from src.models.vpn_key import VPNKey
from src.models.payment import Payment
from src.utils.constants import VPNKeyStatus, PaymentStatus
from src.services.wireguard import WireGuardService

logger = logging.getLogger(__name__)


class VPNService:
    """Сервис для управления VPN ключами"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.wg_manager = WireGuardService()

    async def create_vpn_key(
            self,
            user: User,
            days: int,
            payment: Optional[Payment] = None
    ) -> VPNKey:
        """Создание нового VPN ключа"""
        try:
            # Генерируем уникальное имя для ключа
            key_name = self._generate_key_name(user.telegram_id)

            # Генерируем ключи WireGuard
            keys = await self.wg_manager.generate_keys()

            # Получаем информацию о сервере
            server_info = await self.wg_manager.get_server_info()

            # Получаем свободный IP адрес
            ip_address = await self.wg_manager.get_next_client_ip()

            # Рассчитываем дату истечения
            expires_at = datetime.now() + timedelta(days=days)

            # Генерируем конфиг для клиента
            config_data = await self.wg_manager.generate_client_config(
                client_private_key=keys["private_key"],
                client_ip=ip_address,
                server_public_key=server_info["public_key"],
                server_endpoint=server_info["endpoint"],
                server_port=server_info["port"]
            )

            # Добавляем клиента на сервер
            added = await self.wg_manager.add_client_to_server(keys["public_key"], ip_address)
            if not added:
                raise Exception("Не удалось добавить клиента на сервер WireGuard")

            # Создаем запись в базе данных
            vpn_key = VPNKey(
                key_name=key_name,
                user_id=user.id,
                private_key=keys["private_key"],
                public_key=keys["public_key"],
                server_public_key=server_info["public_key"],
                ip_address=ip_address,
                server_ip=server_info["endpoint"],
                server_port=server_info["port"],
                server_endpoint=server_info["endpoint"],
                days=days,
                expires_at=expires_at,
                status=VPNKeyStatus.ACTIVE.value if payment and payment.is_confirmed else VPNKeyStatus.PENDING.value,
                config_data=config_data,
                payment_id=payment.id if payment else None
            )

            self.session.add(vpn_key)
            await self.session.commit()

            logger.info(f"Создан VPN ключ {key_name} для пользователя {user.telegram_id}")
            return vpn_key

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка создания VPN ключа: {e}")
            raise

    async def revoke_vpn_key(self, key_id: int, admin_id: Optional[int] = None) -> bool:
        """Отзыв VPN ключа"""
        try:
            # Находим ключ
            stmt = select(VPNKey).where(VPNKey.id == key_id)
            result = await self.session.execute(stmt)
            vpn_key = result.scalar_one_or_none()

            if not vpn_key:
                return False

            # Удаляем ключ с сервера
            await self.wg_manager.remove_client_from_server(vpn_key.public_key)

            # Обновляем статус в базе
            vpn_key.status = VPNKeyStatus.REVOKED.value
            await self.session.commit()

            logger.info(f"VPN ключ {vpn_key.key_name} отозван администратором {admin_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка отзыва VPN ключа: {e}")
            return False

    async def get_user_keys(self, user_id: int) -> list[VPNKey]:
        """Получение всех ключей пользователя"""
        stmt = select(VPNKey).where(
            VPNKey.user_id == user_id,
            VPNKey.status == VPNKeyStatus.ACTIVE.value
        ).order_by(VPNKey.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_expired_keys(self) -> list[VPNKey]:
        """Получение списка просроченных ключей"""
        stmt = select(VPNKey).where(
            and_(
                VPNKey.status == VPNKeyStatus.ACTIVE.value,
                VPNKey.expires_at < datetime.now()
            )
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _generate_key_name(self, user_id: int) -> str:
        """Генерация уникального имени ключа"""
        timestamp = int(datetime.now().timestamp())
        random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        return f"user{user_id}_{timestamp}_{random_suffix}"