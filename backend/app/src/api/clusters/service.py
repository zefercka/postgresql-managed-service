from app.src.database import models
from app.src.database.declarations.cluster import ClusterStatusEnum
from app.src.database.repository import ClusterRepository, PostgresVersionRepository
from app.src.dependency import helpers
from app.src.schemas.cluster import Cluster, CreateCluster
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import InvalidVersionError, NotFoundClusterError


async def create_cluster(
    session: AsyncSession, current_user: models.User, cluster: CreateCluster
) -> Cluster:
    """
    Создаёт новый кластер
    """

    existed_version = await PostgresVersionRepository.find_one_or_none(
        session, version=cluster.pg_version
    )
    if existed_version is None:
        raise InvalidVersionError

    data = cluster.model_dump()
    data["id"] = helpers.generate_cluster_id()
    data["owner_id"] = current_user.id

    new_cluster = await ClusterRepository.add(session, **data)

    return Cluster.model_validate(new_cluster)


async def get_cluster(
    session: AsyncSession, current_user: models.User, cluster_id: str
) -> Cluster:
    """
    Возвращает кластер по ID
    """

    existed_cluster = await ClusterRepository.find_one_or_none(session, id=cluster_id)
    if existed_cluster is None or existed_cluster.owner_id != current_user.id:
        raise NotFoundClusterError(cluster_id)

    return Cluster.model_validate(existed_cluster)


async def update_cluster(
    session: AsyncSession,
    current_user: models.User,
    cluster: CreateCluster,
    cluster_id: str,
) -> Cluster:
    """
    Обновляет кластер по ID
    """

    existed_cluster = await ClusterRepository.find_one_or_none(session, id=cluster_id)
    if existed_cluster is None or existed_cluster.owner_id != current_user.id:
        raise NotFoundClusterError(cluster_id)

    existed_version = await PostgresVersionRepository.find_one_or_none(
        session, version=cluster.pg_version
    )
    if existed_version is None:
        raise InvalidVersionError

    cluster_data = cluster.model_dump()
    await ClusterRepository.update(session, id=cluster_id, **cluster_data)

    updated_cluster = await ClusterRepository.find_one_or_none(session, id=cluster_id)

    return Cluster.model_validate(updated_cluster)


async def get_clusters(
    session: AsyncSession, current_user: models.User, limit: int, offset: int
) -> list[Cluster]:
    """
    Возвращает список кластеров, владельцем которых является текущий
    пользователь
    """

    clusters = ClusterRepository.find_user_clusters(
        session, current_user.id, False, limit, offset
    )

    return [Cluster.model_validate(cluster) for cluster in clusters]
