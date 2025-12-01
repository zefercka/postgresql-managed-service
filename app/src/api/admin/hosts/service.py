from datetime import datetime, timezone

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.src.database import models
from app.src.database.repository import HypervHostAuditRepository, HypervHostRepository
from app.src.dependency import helpers
from app.src.schemas.hyperv_host import (
    CreateHypervHost,
    HypervHost,
    HypervHostAudit,
    HypervHostResponse,
)

from .exceptions import (
    HostAlreadyExistsError,
    HostCantBeChangedError,
    HostCantBeDeletedError,
    NotFoundHostError,
)


async def create_host(
    session: AsyncSession, current_user: models.User, host: CreateHypervHost
) -> HypervHost:
    """Создаёт новый HyperV хост"""

    existed_host = await HypervHostRepository.find_one_or_none(
        session, host_fqdn=host.host_fqdn
    )
    if existed_host is not None:
        raise HostAlreadyExistsError

    data = host.model_dump()
    data["free_storage"] = data["total_storage"]
    data["free_ram"] = data["total_ram"]
    data["free_cpu"] = data["total_cpu"]

    new_host = await HypervHostRepository.add(session, **data)
    await HypervHostAuditRepository.add(
        session,
        user_id=current_user.id,
        hyperv_host_id=new_host.id,
        log="HyperV хост создан",
    )

    return HypervHost.model_validate(new_host)


async def get_host(
    session: AsyncSession, current_user: models.User, host_id: int
) -> HypervHost:
    """Возвращает HyperV хост"""

    host = await HypervHostRepository.find_one_or_none(session, id=host_id)
    if host is None:
        raise NotFoundHostError

    return HypervHost.model_validate(host)


async def delete_host(session: AsyncSession, current_user: models.User, host_id: int):
    """Удалить HyperV хост по ID"""

    existed_host = await HypervHostRepository.find_one_or_none(session, id=host_id)
    if existed_host is None:
        raise NotFoundHostError

    clusters_on_host = await HypervHostRepository.count_clusters_on_host(
        session, host_id
    )
    if clusters_on_host != 0:
        raise HostCantBeDeletedError

    await HypervHostRepository.update(
        session, host_id, deleted_at=datetime.now(timezone.utc)
    )
    await HypervHostAuditRepository.add(
        session,
        user_id=current_user.id,
        hyperv_host_id=host_id,
        log="Сервер удалён",
    )


async def update_host(
    session: AsyncSession,
    current_user: models.User,
    host: CreateHypervHost,
    host_id: int,
) -> HypervHost:
    """Обновить HyperV хост по ID"""

    existed_host = await HypervHostRepository.find_one_or_none(session, id=host_id)
    if existed_host is None:
        raise NotFoundHostError

    add_storage = host.total_storage - existed_host.total_storage
    add_ram = host.total_ram - existed_host.total_ram
    add_cpu = host.total_cpu - existed_host.total_cpu

    if any(
        [
            existed_host.free_storage + add_storage < 0,
            existed_host.free_ram + add_ram < 0,
            existed_host.free_cpu + add_cpu < 0,
        ]
    ):
        raise HostCantBeChangedError

    data = host.model_dump()
    data["free_storage"] = existed_host.free_storage + add_storage
    data["free_ram"] = existed_host.free_ram + add_ram
    data["free_cpu"] = existed_host.free_cpu + add_cpu

    existed_host = existed_host.dict()

    await HypervHostRepository.update(session, host_id, **data)
    updated_host = await HypervHostRepository.find_one_or_none(session, id=host_id)

    audit = helpers.generate_audit_log(existed_host, updated_host.dict())

    if audit is not None:
        await HypervHostAuditRepository.add(
            session,
            user_id=current_user.id,
            hyperv_host_id=host_id,
            log=audit,
        )

    return HypervHost.model_validate(updated_host)


async def get_hosts(
    session: AsyncSession,
    current_user: models.User,
    show_deleted: bool,
    limit: int,
    offset: int,
) -> HypervHostResponse:
    """Возвращает список всех HyperV хостов"""

    hosts, total = await HypervHostRepository.find_all(
        session, show_deleted, limit, offset
    )

    return HypervHostResponse.model_validate(
        {
            "hosts": [host for host in hosts],
            "total": total,
        }
    )


async def get_audit(
    session: AsyncSession, current_user: models.User, host_id: int
) -> list[HypervHostAudit]:
    """Возвращает логи изменения для HyperV хоста"""

    existed_host = await HypervHostRepository.find_one_or_none(session, id=host_id)
    if existed_host is None:
        raise NotFoundHostError

    audit = await HypervHostAuditRepository.find_all(
        session, limit=100, hyperv_host_id=host_id
    )

    return [HypervHostAudit.model_validate(log) for log in audit]
