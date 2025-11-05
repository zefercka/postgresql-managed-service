from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta

T = TypeVar("T", bound=DeclarativeMeta)


class BaseRepository(Generic[T]):
    model: Type[T]

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, **filter) -> Optional[T]:
        query = select(cls.model).filter_by(**filter).limit(1)
        result = await session.execute(query)
        return result.scalars().one_or_none()

    @classmethod
    async def add(cls, session: AsyncSession, **data) -> T:
        new_item = cls.model(**data)
        session.add(new_item)

        await session.flush()

        return new_item

    @classmethod
    async def update(cls, session: AsyncSession, id: int, **data) -> None:
        query = update(cls.model).where(cls.id == id).values(**data)
        await session.execute(query)

    @classmethod
    async def find_all(
        cls, session: AsyncSession, limit: int = 50, offset: int = 0, **filter
    ) -> list[T]:
        query = select(cls.model).limit(limit).offset(offset)

        if filter:
            query = query.filter_by(**filter)

        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def count(cls, session: AsyncSession, **filter) -> int:
        query = select(func.count()).select_from(cls.model)

        if filter:
            query = query.filter_by(**filter)

        result = await session.execute(query)
        return result.scalar()

    @classmethod
    async def delete(cls, session: AsyncSession, id: int) -> None:
        primary_key_name = cls.model.__table__.primary_key.columns.keys()[0]
        primary_key_column = getattr(cls.model, primary_key_name)

        query = delete(cls.model).where(primary_key_column == id)
        await session.execute(query)
