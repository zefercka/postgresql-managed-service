from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.src.database import Base
from app.src.database.declarations.user import UserPermissionLevelEnum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
        nullable=False,
        comment="Идентификатор пользователя",
    )
    tg_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, comment="Идентификатор пользователя в телеграмме"
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(64), unique=True, comment="Имя пользователя в телеграмме"
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(64), comment="Настоящее имя пользователя"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(64), comment="Фамилия пользователя"
    )
    is_verified: Mapped[bool] = mapped_column(
        default=False,
        comment="Подтвержден ли аккаунт пользователя",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Дата и время последней активности",
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        default=True, nullable=False, comment="Включены ли уведомления"
    )
    permission_level: Mapped[int] = mapped_column(
        default=UserPermissionLevelEnum.USER, comment="Уровень доступа"
    )
