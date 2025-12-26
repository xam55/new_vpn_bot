from sqlalchemy.orm import relationship
from sqlalchemy import String, BigInteger, Boolean, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from src.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    total_spent: Mapped[float] = mapped_column(Float, default=0.0)
    keys_created: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 🔥 ВОТ ЧЕГО НЕ ХВАТАЛО
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}" if self.last_name else self.first_name

    def __repr__(self):
        return f"User(id={self.id}, telegram_id={self.telegram_id})"


# 🔽 остальные relationship — после класса
if TYPE_CHECKING:
    from .vpn_key import VPNKey
    from .payment import Payment

User.vpn_keys = relationship("VPNKey", back_populates="user")
