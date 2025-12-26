from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.src.database import Base
from app.src.database.declarations.cluster_users import ClusterUserStatusEnum


class ClusterUserStatus(Base):
    __tablename__ = "cluster_user_statuses"

    id: Mapped[int] = mapped_column(
        autoincrement=False, primary_key=True, comment="Идентификатор статуса"
    )
    status: Mapped[str] = mapped_column(unique=True, comment="Имя статуса")
    description: Mapped[Optional[str]] = mapped_column(comment="Описание статуса")


class ClusterUser(Base):
    __tablename__ = "cluster_users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        autoincrement=False,
        comment="Идентификатор пользователя",
    )
    cluster_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("clusters.id", onupdate="restrict", ondelete="restrict"),
        comment="Идентификатор кластера",
    )
    status_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cluster_user_statuses.id"),
        default=ClusterUserStatusEnum.CREATING,
        comment="Статус пользователя",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
    )
    username: Mapped[str] = mapped_column(String(64), comment="Имя пользователя")
    permissions: Mapped[str] = mapped_column(
        String(64), comment="Список привилегий пользователя через запятую"
    )

    status: Mapped[ClusterUserStatus] = relationship(
        "ClusterUserStatus", lazy="selectin"
    )


class ClusterUserAudit(Base):
    __tablename__ = "cluster_users_audit"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="restrict", ondelete="restrict"),
        comment="Пользователь совершивший действие",
    )
    cluster_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cluster_users.id", onupdate="restrict", ondelete="restrict"),
        comment="Пользователь кластера над которым произошло изменение",
    )
    log: Mapped[str] = mapped_column(comment="Лог изменений")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="Время создания лога",
    )
