from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.src.database import Base
from app.src.database.declarations.hyperv_hosts import HypervHostStatusEnum


class HypervHostStatus(Base):
    __tablename__ = "hyperv_hosts_statuses"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=False,
        comment="Идентификатор статуса",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        comment="Статус",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(256), comment="Описание статуса"
    )


class HypervHost(Base):
    __tablename__ = "hyperv_hosts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="Идентификатор хоста",
    )
    host_fqdn: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="Адрес хоста",
    )
    winrm_port: Mapped[int] = mapped_column(
        comment="Порт WinRM",
    )
    https: Mapped[bool] = mapped_column(
        comment="Используется ли HTTPS для подключения",
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(128), comment="Локация сервера"
    )
    description: Mapped[Optional[str]] = mapped_column(
        comment="Дополнительное описание сервера"
    )

    status_id: Mapped[int] = mapped_column(
        ForeignKey(
            "hyperv_hosts_statuses.id", onupdate="restrict", ondelete="restrict"
        ),
        default=HypervHostStatusEnum.ON_SERVICE,
        comment="Хост Hyper-V, на котором размещён кластер",
    )

    total_storage: Mapped[int] = mapped_column(
        comment="Общий объем хранилища в ГБ",
    )
    total_ram: Mapped[int] = mapped_column(
        comment="Общий объем оперативной памяти в МБ",
    )
    total_cpu: Mapped[int] = mapped_column(
        comment="Общее кол-во ядер процессора",
    )

    free_storage: Mapped[int] = mapped_column(
        comment="Свободный объем хранилища в ГБ",
    )
    free_ram: Mapped[int] = mapped_column(
        comment="Свободный объем оперативной памяти в МБ",
    )
    free_cpu: Mapped[int] = mapped_column(
        comment="Свободное кол-во ядер процессора",
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

    disks_path: Mapped[str] = mapped_column(String(260))

    status: Mapped[HypervHostStatus] = relationship("HypervHostStatus", lazy="selectin")


class HypervHostAudit(Base):
    __tablename__ = "hyperv_hosts_audit"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="restrict", ondelete="restrict"),
        comment="Пользователь совершивший действие",
    )
    hyperv_host_id: Mapped[int] = mapped_column(
        ForeignKey("hyperv_hosts.id", onupdate="restrict", ondelete="restrict"),
        comment="HyperV хост над которым было совершенно действие",
    )
    log: Mapped[str] = mapped_column(comment="Лог изменений")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="Время создания лога",
    )
