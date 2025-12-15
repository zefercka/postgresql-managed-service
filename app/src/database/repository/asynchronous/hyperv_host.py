from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.src.database.models.cluster import Cluster
from app.src.database.models.hyperv_host import HypervHost, HypervHostAudit

from . import BaseRepository


class HypervHostRepository(BaseRepository[HypervHost]):
    model = HypervHost

    @staticmethod
    async def add(session: AsyncSession, **data) -> HypervHost:
        new_item = HypervHost(**data)
        session.add(new_item)

        await session.flush()

        result = await session.execute(
            select(HypervHost)
            .options(selectinload(HypervHost.status))
            .where(HypervHost.id == new_item.id)
        )

        return result.scalar_one()

    @staticmethod
    async def find_host_with_resources(
        session: AsyncSession, cpu: int, storage: int, ram: int, **filter
    ) -> Optional[HypervHost]:
        """Возвращает один HyperV хост с необходимым кол-вом
        свободных ресурсов, можно добавить доп. фильтры

        Args:
            session (AsyncSession): Сессия БД
            cpu (int): Необходимое кол-во CPU
            storage (int): Необходимый объём дискового пространства в ГБ
            ram (int): Необходимый объём RAM в МБ

        Returns:
            Optional[HypervHost]: Найденный хост
        """
        query = (
            select(HypervHost)
            .where(
                and_(
                    HypervHost.free_cpu >= cpu,
                    HypervHost.free_storage >= storage,
                    HypervHost.free_ram >= ram,
                    HypervHost.deleted_at == None,
                )
            )
            .limit(1)
        )

        if filter:
            query = query.filter_by(**filter)

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def find_all(
        session: AsyncSession,
        show_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[HypervHost], int]:
        """Поиск всех HyperV хостов. Возвращает хосты и их общее кол-во

        Args:
            session (AsyncSession): Сессия БД
            limit (int, optional): Лимит по выборке. По умолчанию 50.
            offset (int, optional): Сдвиг по выборке. По умолчанию 0.

        Returns:
            tuple[list[HypervHost], int]: Хосты и их общее кол-во
        """

        query = (
            select(HypervHost).order_by(HypervHost.id.asc()).limit(limit).offset(offset)
        )
        if not show_deleted:
            query = query.where(HypervHost.deleted_at == None)

        result = await session.execute(query)
        hosts = result.scalars().all()

        query = select(func.count(HypervHost.id))
        if not show_deleted:
            query = query.where(HypervHost.deleted_at == None)

        result = await session.execute(query)
        total = result.scalar_one()

        return hosts, total

    @staticmethod
    async def count_clusters_on_host(
        session: AsyncSession,
        host_id: int,
    ) -> int:
        """Считает кол-во кластеров, которые не удалены и используют
        этот HyperV хост

        Args:
            session (AsyncSession): Сессия БД
            host_id (int): Идентификатор хоста

        Returns:
            int: Кол-во кластеров, работающих на этом хосте
        """
        query = select(func.count(Cluster.id)).where(
            and_(Cluster.hyperv_host_id == host_id, Cluster.deleted_at == None)  # noqa: E711
        )

        result = await session.execute(query)
        total = result.scalar_one()

        return total

    @staticmethod
    async def find_clusters_on_host(
        session: AsyncSession,
        host_id: int,
    ) -> list[Cluster]:
        """Возвращает список кластеров, работающих на данном HyperV хосте

        Args:
            session (AsyncSession): Сессия БД
            host_id (int): Идентификатор хоста

        Returns:
            list[Cluster]: Список кластеров
        """
        query = select(Cluster).where(
            and_(Cluster.hyperv_host_id == host_id, Cluster.deleted_at == None)  # noqa: E711
        )

        result = await session.execute(query)
        clusters = result.scalars().all()

        return clusters


class HypervHostAuditRepository(BaseRepository[HypervHostAudit]):
    model = HypervHostAudit
