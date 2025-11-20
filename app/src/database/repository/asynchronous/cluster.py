from app.src.database.declarations import ClusterStatusEnum
from app.src.database.models import Cluster, PostgresVersion
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    ) -> list[Cluster]:
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
        return result.scalars().all()


class PostgresVersionRepository(BaseRepository[PostgresVersion]):
    model = PostgresVersion
