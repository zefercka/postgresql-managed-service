from typing import Annotated

from app.config import settings
from fastapi import Depends
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


if settings.REPOSITORY_TYPE == "async":
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def get_db():
        async with SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    AsyncDbSession = Annotated[AsyncSession, Depends(get_db)]

elif settings.REPOSITORY_TYPE == "sync":
    from contextlib import contextmanager

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)

    SessionLocal = sessionmaker(engine, expire_on_commit=False)

    @contextmanager
    def get_db():
        with SessionLocal() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
