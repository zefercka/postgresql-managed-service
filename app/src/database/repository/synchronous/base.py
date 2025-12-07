from typing import Optional, Type, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import DeclarativeMeta, Session

T = TypeVar("T", bound=DeclarativeMeta)


class BaseRepository[T]:
    model: Type[T]

    @classmethod
    def find_one_or_none(cls, session: Session, **filter) -> Optional[T]:
        query = select(cls.model).filter_by(**filter).limit(1)
        result = session.execute(query)
        return result.scalars().one_or_none()

    @classmethod
    def add(cls, session: Session, **data) -> T:
        new_item = cls.model(**data)
        session.add(new_item)

        session.flush()

        return new_item

    @classmethod
    def update(cls, session: Session, id: int, **data) -> None:
        primary_key_name = cls.model.__table__.primary_key.columns.keys()[0]
        primary_key_column = getattr(cls.model, primary_key_name)

        query = update(cls.model).where(primary_key_column == id).values(**data)
        session.execute(query)

    @classmethod
    def find_all(
        cls, session: Session, limit: int = 50, offset: int = 0, **filter
    ) -> list[T]:
        query = select(cls.model).limit(limit).offset(offset)

        if filter:
            query = query.filter_by(**filter)

        result = session.execute(query)
        return result.scalars().all()

    @classmethod
    def count(cls, session: Session, **filter) -> int:
        query = select(func.count()).select_from(cls.model)

        if filter:
            query = query.filter_by(**filter)

        result = session.execute(query)
        return result.scalar()

    @classmethod
    def delete(cls, session: Session, id: int) -> None:
        primary_key_name = cls.model.__table__.primary_key.columns.keys()[0]
        primary_key_column = getattr(cls.model, primary_key_name)

        query = delete(cls.model).where(primary_key_column == id)
        session.execute(query)
