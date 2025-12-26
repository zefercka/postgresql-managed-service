from fastapi import APIRouter

from app.src.database import AsyncDbSession
from app.src.dependency.auth import CurrentUserAdmin
from app.src.schemas.hyperv_host import (
    CreateHypervHost,
    HypervHost,
    HypervHostAudit,
    HypervHostResponse,
    UpdateHypervHost,
    UpdateHypervHostStatus,
)

from . import service

app = APIRouter(prefix="/hosts")


@app.post("", summary="Создать новый HyperV хост")
async def create_host(
    session: AsyncDbSession, current_user: CurrentUserAdmin, host: CreateHypervHost
) -> HypervHost:
    host = await service.create_host(session, current_user, host)

    return host


@app.get("/{host_id}", summary="Получить HyperV хост по ID")
async def get_host(
    session: AsyncDbSession, current_user: CurrentUserAdmin, host_id: int
) -> HypervHost:
    host = await service.get_host(session, current_user, host_id)

    return host


@app.put("/{host_id}", summary="Обновить HyperV хост по ID")
async def update_host(
    session: AsyncDbSession,
    current_user: CurrentUserAdmin,
    host: UpdateHypervHost,
    host_id: int,
) -> HypervHost:
    host = await service.update_host(session, current_user, host, host_id)

    return host


@app.delete("/{host_id}", summary="Удалить HyperV хост по ID")
async def delete_host(
    session: AsyncDbSession, current_user: CurrentUserAdmin, host_id: int
):
    await service.delete_host(session, current_user, host_id)


@app.get("", summary="Получить список всех HyperV хостов")
async def get_hosts(
    session: AsyncDbSession,
    current_user: CurrentUserAdmin,
    show_deleted: bool = False,
    limit: int = 32,
    offset: int = 0,
) -> HypervHostResponse:
    hosts = await service.get_hosts(session, current_user, show_deleted, limit, offset)

    return hosts


@app.get(
    "/{host_id}/audit", summary="Получить последние 100 событий изменения сервера по ID"
)
async def get_host_audit(
    session: AsyncDbSession, current_user: CurrentUserAdmin, host_id: int
) -> list[HypervHostAudit]:
    audit = await service.get_audit(session, current_user, host_id)

    return audit


@app.get(
    "/{host_id}/clusters", summary="Получить список кластеров на HyperV хосте по ID"
)
async def get_host_clusters(
    session: AsyncDbSession, current_user: CurrentUserAdmin, host_id: int
) -> list[HypervHost]:
    clusters = await service.get_host_clusters(session, current_user, host_id)

    return clusters


@app.patch("/{host_id}/status", summary="Изменить статус HyperV хоста по ID")
async def update_host_status(
    session: AsyncDbSession,
    current_user: CurrentUserAdmin,
    status: UpdateHypervHostStatus,
    host_id: int,
) -> HypervHost:
    host = await service.update_host_status(session, current_user, status, host_id)

    return host
