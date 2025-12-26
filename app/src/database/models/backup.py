from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.src.database import Base
from app.src.database.declarations import BackupStatusEnum, BackupTypeEnum


class BackupStatus(Base):
    __tablename__ = "backup_statuses"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=False, comment="Идентификатор статуса"
    )
    status: Mapped[str] = mapped_column(String(32), unique=True, comment="Статус")
    description: Mapped[Optional[str]] = mapped_column(
        String(256), comment="Описание статуса"
    )


class BackupType(Base):
    __tablename__ = "backup_types"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=False, comment="Идентификатор типа бекапа"
    )
    type: Mapped[str] = mapped_column(String(32), unique=True, comment="Тип бекапа")
    description: Mapped[Optional[str]] = mapped_column(
        String(256), comment="Описание типа бекапа"
    )


class Backup(Base):
    __tablename__ = "backups"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        autoincrement=False,
        comment="Идентификатор бекапа (UUID)",
    )
    cluster_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("clusters.id", onupdate="restrict", ondelete="restrict"),
        comment="Идентификатор кластера, для которого создан бекап",
    )
    name: Mapped[str] = mapped_column(
        String(128),
        comment="Название бекапа, которое ему дал пользователь или система",
    )
    status_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("backup_statuses.id"),
        default=BackupStatusEnum.CREATING,
        comment="Идентификатор текущего статуса бекапа",
    )
    type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("backup_types.id"),
        default=BackupTypeEnum.MANUAL,
        comment="Идентификатор типа бекапа",
    )
    s3_bucket: Mapped[str] = mapped_column(
        String(255), comment="Имя S3 бакета, где хранится бекап"
    )
    s3_key: Mapped[str] = mapped_column(
        String(1024), comment="Путь к файлу бекапа в S3"
    )
    s3_region: Mapped[Optional[str]] = mapped_column(
        String(64), comment="Регион S3, где хранится бекап"
    )
    size_bytes: Mapped[Optional[int]] = mapped_column(
        BigInteger, comment="Размер бекапа в байтах"
    )
    pg_version: Mapped[str] = mapped_column(
        String(64), comment="Версия PostgreSQL, с которой был создан бекап"
    )
    compression: Mapped[Optional[str]] = mapped_column(
        String(32), comment="Тип сжатия бекапа (gzip, zstd, none)"
    )
    backup_method: Mapped[Optional[str]] = mapped_column(
        String(64), comment="Метод создания бекапа"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, comment="Сообщение об ошибке, если бекап не был создан"
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="restrict", ondelete="restrict"),
        comment="Пользователь, который создал бекап (null для автоматических)",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="Дата и время начала создания бекапа",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="Дата и время завершения создания бекапа",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="Дата и время удаления бекапа"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="Дата и время истечения срока хранения бекапа",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    status: Mapped[BackupStatus] = relationship("BackupStatus", lazy="selectin")
    type: Mapped[BackupType] = relationship("BackupType", lazy="selectin")
