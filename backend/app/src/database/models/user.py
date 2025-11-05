from datetime import datetime, timezone
from typing import Optional

from app.src.database import Base
from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
        nullable=False,
        comment="Идентификатор пользователя",
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger, nullable=True, comment="Идентификатор пользователя в телеграмме"
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=True, comment="Имя пользователя в телеграмме"
    )
    first_name: Mapped[str] = mapped_column(
        String(64), nullable=True, comment="Настоящее имя пользователя"
    )
    last_name: Mapped[str] = mapped_column(
        String(64), nullable=True, comment="Фамилия пользователя"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Подтвержден ли аккаунт пользователя",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        comment="Дата и время последней активности",
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Включены ли уведомления"
    )
