from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.src.database.models import ClusterUser, ClusterUserAudit

from . import BaseRepository


class ClusterUserRepository(BaseRepository[ClusterUser]):
    model = ClusterUser

    @classmethod
    async def find_one_or_none_with_status(
        cls, session: AsyncSession, **filter
    ) -> ClusterUser | None:
        """
        Получить пользователя кластера с информацией о статусе
        """
        query = (
            select(cls.model)
            .options(selectinload(cls.model.status))
            .filter_by(**filter)
            .limit(1)
        )

        result = await session.execute(query)
        return result.scalars().one_or_none()

    @classmethod
    async def find_all_with_status(
        cls,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        show_deleted: bool = False,
        **filter,
    ) -> list[ClusterUser]:
        """
        Получить всех пользователей кластера с информацией о статусе
        """
        query = (
            select(cls.model)
            .options(selectinload(cls.model.status))
            .limit(limit)
            .offset(offset)
        )

        if filter:
            query = query.filter_by(**filter)

        # Если show_deleted=False, фильтруем удалённых пользователей
        if not show_deleted:
            query = query.filter(cls.model.deleted_at.is_(None))

        result = await session.execute(query)
        return result.scalars().all()


class ClusterUserAuditRepository(BaseRepository[ClusterUserAudit]):
    model = ClusterUserAudit
