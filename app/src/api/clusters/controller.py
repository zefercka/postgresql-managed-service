from fastapi import APIRouter

from app.src.database import AsyncDbSession
from app.src.dependency.auth import CurrentUser
from app.src.schemas.cluster import (
    Cluster,
    CreateCluster,
    GetClustersResponse,
)

from . import service

app = APIRouter(prefix="/clusters")


@app.post("", summary="Создание нового кластера")
async def create_cluster(
    session: AsyncDbSession, current_user: CurrentUser, cluster: CreateCluster
) -> Cluster:
    cluster = await service.create_cluster(session, current_user, cluster)

    return cluster


@app.get("/{cluster_id}", summary="Получить кластер по ID")
async def get_cluster(
    session: AsyncDbSession, current_user: CurrentUser, cluster_id: str
) -> Cluster:
    cluster = await service.get_cluster(session, current_user, cluster_id)

    return cluster


@app.put("/{cluster_id}", summary="Обновить кластер по ID")
async def update_cluster(
    session: AsyncDbSession, current_user: CurrentUser, cluster: CreateCluster
) -> Cluster:
    cluster = await service.update_cluster(session, current_user, cluster)

    return cluster


@app.get("", summary="Получить список кластеров текущего пользователя")
async def get_clusters(
    session: AsyncDbSession, current_user: CurrentUser, limit: int = 8, offset: int = 0
) -> GetClustersResponse:
    clusters = await service.get_clusters(session, current_user, limit, offset)

    return clusters
