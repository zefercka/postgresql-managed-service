from app.src.database.models import User
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    @staticmethod
    async def is_email_free(session: AsyncSession, email: str):
        query = select(exists().where(User.email == email))

        result = await session.execute(query)
        return not result.scalars().first()

    @staticmethod
    async def is_username_free(session: AsyncSession, username: str):
        query = select(exists().where(User.username == username))

        result = await session.execute(query)
        return not result.scalars().first()
