from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import TYPE_CHECKING

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.user import User


class AdminLog(Base):
    """Модель лога действий администратора"""
    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Кто совершил действие
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    admin: Mapped["User | None"] = relationship()

    # Над кем/чем совершено действие
    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_user: Mapped["User | None"] = relationship(foreign_keys=[target_user_id])

    target_key_id: Mapped[int | None] = mapped_column(ForeignKey("vpn_keys.id", ondelete="SET NULL"), nullable=True)
    target_payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)

    # Детали действия
    action_type: Mapped[str] = mapped_column(String(50),
                                             nullable=False)  # Пример: "key_create", "key_delete", "user_ban"
    action_details: Mapped[str] = mapped_column(Text, nullable=False)  # JSON с деталями

    # IP адрес (если доступен)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Дата и время
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"AdminLog(id={self.id}, action={self.action_type}, admin_id={self.admin_id})"