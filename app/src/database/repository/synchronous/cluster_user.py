from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.src.database.models import ClusterUser, ClusterUserAudit

from . import BaseRepository


class ClusterUserRepository(BaseRepository[ClusterUser]):
    model = ClusterUser

    @staticmethod
    def find_one_or_none_with_status(session: Session, **filter) -> ClusterUser | None:
        """
        Получить пользователя кластера с информацией о статусе
        """
        query = (
            select(ClusterUser)
            .options(selectinload(ClusterUser.status))
            .filter_by(**filter)
            .limit(1)
        )

        result = session.execute(query)
        return result.scalars().one_or_none()

    @staticmethod
    def find_all_with_status(
        session: Session,
        limit: int = 50,
        offset: int = 0,
        show_deleted: bool = False,
        **filter,
    ) -> list[ClusterUser]:
        """
        Получить всех пользователей кластера с информацией о статусе
        """
        query = (
            select(ClusterUser)
            .options(selectinload(ClusterUser.status))
            .limit(limit)
            .offset(offset)
        )

        if filter:
            query = query.filter_by(**filter)

        if not show_deleted:
            query = query.filter(ClusterUser.deleted_at.is_(None))

        result = session.execute(query)
        return result.scalars().all()


class ClusterUserAuditRepository(BaseRepository[ClusterUserAudit]):
    model = ClusterUserAudit
