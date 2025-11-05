from app.config import settings

if settings.REPOSITORY_TYPE == "async":
    from .core import AsyncDbSession, Base, get_db
elif settings.REPOSITORY_TYPE == "sync":
    from .core import Base, get_db

from . import repository
