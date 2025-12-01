from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.src.database import Base
from app.src.database.declarations import ClusterStatusEnum


class ClusterStatus(Base):
    __tablename__ = "cluster_statuses"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=False, comment="Идентификатор статуса"
    )
    status: Mapped[str] = mapped_column(String(32), unique=True, comment="Статус")
    description: Mapped[Optional[str]] = mapped_column(
        String(256), comment="Описание статуса"
    )


class PostgresVersion(Base):
    __tablename__ = "postgres_versions"

    version: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="Версия постгрес"
    )


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        autoincrement=False,
        comment="Идентификатор кластера",
    )
    name: Mapped[str] = mapped_column(
        String(64),
        comment="Название кластера, которое ему дал пользователь",
    )
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="restrict", ondelete="restrict"),
        comment="Пользователь, который создал этот кластер",
    )
    status_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cluster_statuses.id"),
        default=ClusterStatusEnum.CREATING,
        comment="Идентификатор текущего статуса кластера",
    )
    pg_version: Mapped[str] = mapped_column(
        String(64),
        ForeignKey(
            "postgres_versions.version", onupdate="restrict", ondelete="restrict"
        ),
        comment="Версия PostgreSQL",
    )
    cpu: Mapped[int] = mapped_column(comment="Количество vCPU на хосте кластера")
    ram_mb: Mapped[int] = mapped_column(comment="Объём ОЗУ в МБ")
    storage_gb: Mapped[int] = mapped_column(comment="Объём диска для хранилища в ГБ")
    hyperv_host_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("hyperv_hosts.id", onupdate="restrict", ondelete="restrict"),
        comment="Хост Hyper-V, на котором размещён кластер",
    )
    postgres_port: Mapped[Optional[int]] = mapped_column(
        comment="Порт хоста на который прокинут PostgreSQL порт из вм"
    )
    ssh_port: Mapped[Optional[int]] = mapped_column(
        comment="Порт хоста на который прокинут ssh порт из вм"
    )
    host_fqdn: Mapped[Optional[str]] = mapped_column(
        comment="Адрес ВМ внутри NAT сети"
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
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    status: Mapped[ClusterStatus] = relationship("ClusterStatus", lazy="selectin")
