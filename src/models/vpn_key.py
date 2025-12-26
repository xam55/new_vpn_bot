
# relationship после определения класса (в самом конце файла)

from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from src.models.base import Base

if TYPE_CHECKING:
    from .user import User
    from .payment import Payment


class VPNKey(Base):
    __tablename__ = "vpn_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    key_name: Mapped[str] = mapped_column(String(100), unique=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="vpn_keys")

    private_key: Mapped[str] = mapped_column(Text)
    public_key: Mapped[str] = mapped_column(String(100))
    
    server_public_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    server_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    server_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    server_endpoint: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    ip_address: Mapped[str] = mapped_column(String(20))
    config_data: Mapped[str] = mapped_column(Text)

    days: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    status: Mapped[str] = mapped_column(String(20), default="active")

    payment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("payments.id"), nullable=True)
    payment: Mapped[Optional["Payment"]] = relationship(back_populates="vpn_key")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at and self.days:
            self.expires_at = datetime.now() + timedelta(days=self.days)

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.expires_at > datetime.now()

    @property
    def days_left(self) -> int:
        if not self.is_active:
            return 0
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)

    def __repr__(self):
        return f"VPNKey(id={self.id}, name={self.key_name})"


