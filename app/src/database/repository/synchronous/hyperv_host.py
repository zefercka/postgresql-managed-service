from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload

from app.src.database.models import HypervHost

from . import BaseRepository


class HypervHostRepository(BaseRepository[HypervHost]):
    model = HypervHost

    @staticmethod
    def add(session: Session, **data) -> HypervHost:
        new_item = HypervHost(**data)
        session.add(new_item)

        session.flush()

        result = session.execute(
            select(HypervHost)
            .options(selectinload(HypervHost.status))
            .where(HypervHost.id == new_item.id)
        )

        return result.scalar_one()

    @staticmethod
    def find_host_with_resources(
        session: Session, cpu: int, storage: int, ram: int, **filter
    ) -> Optional[HypervHost]:
        """Возвращает один HyperV хост с необходимым кол-вом
        свободных ресурсов, можно добавить доп. фильтры

        Args:
            session (Session): Сессия БД
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
                )
            )
            .limit(1)
        )

        if filter:
            query = query.filter_by(**filter)

        result = session.execute(query)

        return result.scalar_one_or_none()
