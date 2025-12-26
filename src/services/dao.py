from typing import Optional, List
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.models.user import User
from src.models.vpn_key import VPNKey
from src.models.payment import Payment


# ========== USER DAO ==========
class UserDAO:
    @staticmethod
    async def get_or_create(session: AsyncSession, telegram_id: int, **kwargs) -> User:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id, **kwargs)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user

    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_admins(session: AsyncSession) -> List[User]:
        result = await session.execute(select(User).where(User.is_admin == True))
        return list(result.scalars().all())


# ========== VPN KEY DAO ==========
class VPNKeyDAO:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        key_name: str,
        private_key: str,
        public_key: str,
        ip_address: str,
        config_data: str,
        days: int,
        **kwargs
    ) -> VPNKey:
        key = VPNKey(
            user_id=user_id,
            key_name=key_name,
            private_key=private_key,
            public_key=public_key,
            ip_address=ip_address,
            config_data=config_data,
            days=days,
            **kwargs
        )

        session.add(key)
        await session.commit()
        await session.refresh(key)
        return key


# ========== PAYMENT DAO ==========
class PaymentDAO:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        payment_id: str,
        amount: float,
        method: str,
        payment_details: str
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            payment_id=payment_id,
            amount=amount,
            method=method,
            payment_details=payment_details
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment

    @staticmethod
    async def get_by_payment_id(session: AsyncSession, payment_id: str) -> Optional[Payment]:
        result = await session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_as_paid(
        session: AsyncSession,
        payment_id: int,
        proof_photo_id: str
    ) -> bool:
        stmt = (
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status="paid",
                paid_at=datetime.now(),
                proof_photo_id=proof_photo_id
            )
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def confirm_payment(
        session: AsyncSession,
        payment_id: int,
        admin_id: int,
        comment: str
    ) -> bool:
        stmt = (
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status="confirmed",
                confirmed_at=datetime.now(),
                admin_comment=comment
            )
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    # 🔥 ВОТ ТУТ БЫЛ БАГ — ТЕПЕРЬ ИСПРАВЛЕНО
    @staticmethod
    async def reject_payment(
        session: AsyncSession,
        payment_id: int,
        admin_id: int,
        comment: str
    ) -> bool:
        stmt = (
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status="rejected",
                admin_comment=comment
            )
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
