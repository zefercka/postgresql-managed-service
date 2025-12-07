import logging
from typing import Annotated

from app.src.database import AsyncDbSession
from app.src.database.models import User
from app.src.database.repository import UserRepository
from app.src.dependency import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger(__name__)


security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Введите JWT токен (без префикса 'Bearer')",
)

SecurityDepends = Annotated[HTTPAuthorizationCredentials, Depends(security)]


async def get_current_user(
    session: AsyncDbSession,
    credentials: SecurityDepends,
) -> dict:
    """
    Dependency для получения текущего пользователя из JWT токена.
    Используется для защищенных эндпоинтов в Swagger.
    """

    try:
        token = credentials.credentials
        payload = jwt.verify_jwt(token)
    except ExpiredSignatureError:
        logger.warning("Попытка использования истёкшего токена")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истёк",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        logger.warning("Попытка использования недействительного токена")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный тип токена. Требуется access токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await UserRepository.find_one_or_none(
        session=session, id=int(payload.get("sub"))
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    session: AsyncDbSession,
    credentials: SecurityDepends,
) -> User | None:
    """
    Dependency для опционального получения текущего пользователя из JWT токена.
    Возвращает пользователя, если токен валиден, или None, если токен отсутствует.
    """

    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = jwt.verify_jwt(token)
    except ExpiredSignatureError:
        logger.warning("Попытка использования истёкшего токена")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истёк",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        logger.warning("Попытка использования недействительного токена")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный тип токена. Требуется access токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await UserRepository.find_one_or_none(
        session=session, id=int(payload.get("sub"))
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]


def check_permission_level(permission_level: int):
    def _check_permission(current_user: CurrentUser) -> User:
        if current_user.permission_level >= permission_level:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У пользователя нет прав доступа",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _check_permission


CurrentUserAdmin = Annotated[User, Depends(check_permission_level(2048))]
