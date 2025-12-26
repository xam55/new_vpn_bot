from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from src.models.base import Base

if TYPE_CHECKING:
    from .user import User
    from .vpn_key import VPNKey


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(100), unique=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="payments")

    amount: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(20))

    payment_details: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default="pending")

    proof_photo_id: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    admin_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vpn_key: Mapped[Optional["VPNKey"]] = relationship(back_populates="payment")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(minutes=30)

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    @property
    def is_confirmed(self) -> bool:
        return self.status == "confirmed"

    def __repr__(self):
        return f"Payment(id={self.id}, amount={self.amount}, status={self.status})"



# relationship после определения всех классов (в самом конце файла)
