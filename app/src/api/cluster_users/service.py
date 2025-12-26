from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database import models
from app.src.database.declarations.cluster_users import ClusterUserStatusEnum
from app.src.database.repository import (
    ClusterRepository,
    ClusterUserAuditRepository,
    ClusterUserRepository,
)
from app.src.dependency import helpers
from app.src.schemas.cluster_user import (
    ClusterUser,
    CreateClusterUser,
    GetClusterUsersResponse,
    UpdateClusterUser,
)
from app.src.tasks.create_cluster_user_task import create_cluster_user_task

from ..clusters.exceptions import NotFoundClusterError
from .exceptions import ClusterUserAlreadyExistsError, NotFoundClusterUserError


async def create_cluster_user(
    session: AsyncSession,
    current_user: models.User,
    cluster_id: str,
    cluster_user: CreateClusterUser,
) -> ClusterUser:
    """
    Создаёт нового пользователя кластера
    """

    # Проверяем, что кластер существует и принадлежит текущему пользователю
    existed_cluster = await ClusterRepository.find_one_or_none(session, id=cluster_id)
    if existed_cluster is None or existed_cluster.owner_id != current_user.id:
        raise NotFoundClusterError(cluster_id)

    # Проверяем, не существует ли уже пользователь с таким именем в этом кластере
    existed_user = await ClusterUserRepository.find_one_or_none(
        session, username=cluster_user.username, cluster_id=cluster_id
    )
    if existed_user is not None:
        raise ClusterUserAlreadyExistsError(cluster_user.username)

    data = cluster_user.model_dump()
    data["id"] = helpers.generate_uuid_id()
    data["cluster_id"] = cluster_id
    data["status_id"] = ClusterUserStatusEnum.CREATING

    new_cluster_user = await ClusterUserRepository.add(session, **data)

    # Создаём запись аудита
    await ClusterUserAuditRepository.add(
        session,
        user_id=current_user.id,
        cluster_user_id=new_cluster_user.id,
        log=f"Создан пользователь кластера '{cluster_user.username}'",
    )

    # Получаем созданного пользователя со статусом
    created_user = await ClusterUserRepository.find_one_or_none_with_status(
        session, id=new_cluster_user.id
    )

    create_cluster_user_task.send(new_cluster_user.id)

    return ClusterUser.model_validate(created_user)


async def get_cluster_user(
    session: AsyncSession,
    current_user: models.User,
    cluster_id: str,
    cluster_user_id: str,
) -> ClusterUser:
    """
    Возвращает пользователя кластера по ID
    """

    existed_cluster = await ClusterRepository.find_one_or_none(session, id=cluster_id)
    if existed_cluster is None or existed_cluster.owner_id != current_user.id:
        raise NotFoundClusterError(cluster_id)

    existed_cluster_user = await ClusterUserRepository.find_one_or_none_with_status(
        session, id=cluster_user_id, cluster_id=cluster_id
    )
    if existed_cluster_user is None:
        raise NotFoundClusterUserError(cluster_user_id)

    return ClusterUser.model_validate(existed_cluster_user)


async def update_cluster_user(
    session: AsyncSession,
    current_user: models.User,
    cluster_id: str,
    cluster_user_id: str,
    cluster_user: UpdateClusterUser,
) -> ClusterUser:
    """
    Обновляет пользователя кластера по ID
    """

    # Проверяем, что кластер существует и принадлежит текущему пользователю
    existed_cluster = await ClusterRepository.find_one_or_none(session, id=cluster_id)
    if existed_cluster is None or existed_cluster.owner_id != current_user.id:
        raise NotFoundClusterError(cluster_id)

    existed_cluster_user = await ClusterUserRepository.find_one_or_none(
        session, id=cluster_user_id, cluster_id=cluster_id
    )
    if existed_cluster_user is None:
        raise NotFoundClusterUserError(cluster_user_id)

    # Проверяем, не пытается ли пользователь сменить имя на уже существующее
    if existed_cluster_user.username != cluster_user.username:
        user_with_same_name = await ClusterUserRepository.find_one_or_none(
            session, username=cluster_user.username, cluster_id=cluster_id
        )
        if user_with_same_name is not None:
            raise ClusterUserAlreadyExistsError(cluster_user.username)

    cluster_user_data = cluster_user.model_dump()
    await ClusterUserRepository.update(session, id=cluster_user_id, **cluster_user_data)

    # Создаём запись аудита
    await ClusterUserAuditRepository.add(
        session,
        user_id=current_user.id,
        cluster_user_id=cluster_user_id,
        log=f"Обновлён пользователь кластера '{cluster_user.username}'",
    )

    updated_cluster_user = await ClusterUserRepository.find_one_or_none_with_status(
        session, id=cluster_user_id
    )

    return ClusterUser.model_validate(updated_cluster_user)


async def delete_cluster_user(
    session: AsyncSession,
    current_user: models.User,
    cluster_id: str,
    cluster_user_id: str,
) -> None:
    """
    Помечает пользователя кластера как удалённого
    """

    # Проверяем, что кластер существует и принадлежит текущему пользователю
    existed_cluster = await ClusterRepository.find_one_or_none(session, id=cluster_id)
    if existed_cluster is None or existed_cluster.owner_id != current_user.id:
        raise NotFoundClusterError(cluster_id)

    existed_cluster_user = await ClusterUserRepository.find_one_or_none(
        session, id=cluster_user_id, cluster_id=cluster_id
    )
    if existed_cluster_user is None:
        raise NotFoundClusterUserError(cluster_user_id)

    await ClusterUserRepository.update(
        session,
        id=cluster_user_id,
        status_id=ClusterUserStatusEnum.DELETED,
        deleted_at=datetime.now(timezone.utc),
    )

    await ClusterUserAuditRepository.add(
        session,
        user_id=current_user.id,
        cluster_user_id=cluster_user_id,
        log=f"Удалён пользователь кластера '{existed_cluster_user.username}'",
    )


async def get_cluster_users(
    session: AsyncSession,
    current_user: models.User,
    cluster_id: str,
    limit: int,
    offset: int,
    show_deleted: bool = False,
) -> GetClusterUsersResponse:
    """
    Возвращает список пользователей кластера
    """

    # Проверяем, что кластер существует и принадлежит текущему пользователю
    existed_cluster = await ClusterRepository.find_one_or_none(session, id=cluster_id)
    if existed_cluster is None or existed_cluster.owner_id != current_user.id:
        raise NotFoundClusterError(cluster_id)

    cluster_users = await ClusterUserRepository.find_all_with_status(
        session,
        limit=limit,
        offset=offset,
        show_deleted=show_deleted,
        cluster_id=cluster_id,
    )
    total = await ClusterUserRepository.count_with_deleted_filter(
        session, show_deleted=show_deleted, cluster_id=cluster_id
    )

    return GetClusterUsersResponse.model_validate(
        {
            "cluster_users": cluster_users,
            "total": total,
        }
    )
