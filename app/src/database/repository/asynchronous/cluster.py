from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.src.database.declarations import ClusterStatusEnum
from app.src.database.models import Cluster, PostgresVersion

from . import BaseRepository


class ClusterRepository(BaseRepository[Cluster]):
    model = Cluster

    @staticmethod
    async def add(session: AsyncSession, **data) -> Cluster:
        new_item = Cluster(**data)
        session.add(new_item)

        await session.flush()

        result = await session.execute(
            select(Cluster)
            .options(selectinload(Cluster.status))
            .where(Cluster.id == new_item.id)
        )

        return result.scalar_one()

    @staticmethod
    async def find_user_clusters(
        session: AsyncSession,
        user_id: int,
        show_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Cluster], int]:
        """Возвращает список кластеров, владельцем которых является
        пользователь, и общее кол-во кластеров пользователя

        Args:
            session (AsyncSession): Сессия БД
            user_id (int): Идентификатор пользователя
            show_deleted (bool, optional): Показывать ли удалённые
            кластеры. По умолчанию False.
            limit (int, optional): Лимит по выборке. По умолчанию 50.
            offset (int, optional): Сдвиг по выборке. По умолчанию 0.

        Returns:
            tuple[list[Cluster], int]: Кластеры и общее кол-во кластеров
            пользователя
        """

        query = (
            select(Cluster)
            .where(
                Cluster.owner_id == user_id,
            )
            .order_by(Cluster.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if not show_deleted:
            query = query.where(Cluster.status_id != ClusterStatusEnum.DELETED)

        result = await session.execute(query)
        clusters = result.scalars().all()

        query = select(func.count(Cluster.id)).where(
            Cluster.owner_id == user_id,
        )

        if not show_deleted:
            query = query.where(Cluster.status_id != ClusterStatusEnum.DELETED)

        result = await session.execute(query)
        total = result.scalar_one()

        return clusters, total


class PostgresVersionRepository(BaseRepository[PostgresVersion]):
    model = PostgresVersion
