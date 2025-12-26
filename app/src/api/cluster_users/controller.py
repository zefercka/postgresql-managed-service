from fastapi import APIRouter, status

from app.src.database import AsyncDbSession
from app.src.dependency.auth import CurrentUser
from app.src.schemas.cluster_user import (
    ClusterUser,
    CreateClusterUser,
    GetClusterUsersResponse,
    UpdateClusterUser,
)

from . import service

app = APIRouter()


@app.post(
    "/clusters/{cluster_id}/users",
    summary="Создание нового пользователя кластера",
    status_code=status.HTTP_201_CREATED,
)
async def create_cluster_user(
    session: AsyncDbSession,
    current_user: CurrentUser,
    cluster_id: str,
    cluster_user: CreateClusterUser,
) -> ClusterUser:
    """
    Создаёт нового пользователя кластера PostgreSQL
    """
    cluster_user = await service.create_cluster_user(
        session, current_user, cluster_id, cluster_user
    )

    return cluster_user


@app.get(
    "/clusters/{cluster_id}/users/{cluster_user_id}",
    summary="Получить пользователя кластера по ID",
)
async def get_cluster_user(
    session: AsyncDbSession,
    current_user: CurrentUser,
    cluster_id: str,
    cluster_user_id: str,
) -> ClusterUser:
    """
    Возвращает информацию о пользователе кластера по его ID
    """
    cluster_user = await service.get_cluster_user(
        session, current_user, cluster_id, cluster_user_id
    )

    return cluster_user


@app.put(
    "/clusters/{cluster_id}/users/{cluster_user_id}",
    summary="Обновить пользователя кластера по ID",
)
async def update_cluster_user(
    session: AsyncDbSession,
    current_user: CurrentUser,
    cluster_id: str,
    cluster_user_id: str,
    cluster_user: UpdateClusterUser,
) -> ClusterUser:
    """
    Обновляет информацию о пользователе кластера
    """
    cluster_user = await service.update_cluster_user(
        session, current_user, cluster_id, cluster_user_id, cluster_user
    )

    return cluster_user


@app.delete(
    "/clusters/{cluster_id}/users/{cluster_user_id}",
    summary="Удалить пользователя кластера",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_cluster_user(
    session: AsyncDbSession,
    current_user: CurrentUser,
    cluster_id: str,
    cluster_user_id: str,
) -> None:
    """
    Удаляет пользователя кластера (мягкое удаление)
    """
    await service.delete_cluster_user(
        session, current_user, cluster_id, cluster_user_id
    )


@app.get(
    "/clusters/{cluster_id}/users",
    summary="Получить список пользователей кластера",
)
async def get_cluster_users(
    session: AsyncDbSession,
    current_user: CurrentUser,
    cluster_id: str,
    limit: int = 50,
    offset: int = 0,
    show_deleted: bool = False,
) -> GetClusterUsersResponse:
    """
    Возвращает список пользователей кластера с пагинацией.

    По умолчанию удалённые пользователи не показываются.
    Установите show_deleted=true для их отображения.
    """
    cluster_users = await service.get_cluster_users(
        session, current_user, cluster_id, limit, offset, show_deleted
    )

    return cluster_users
