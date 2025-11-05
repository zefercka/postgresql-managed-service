from app.config import settings

if settings.REPOSITORY_TYPE == "async":
    from .asynchronous import *
elif settings.REPOSITORY_TYPE == "sync":
    from .synchronous import *
