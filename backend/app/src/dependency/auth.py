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


async def get_current_user(
    session: AsyncDbSession,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency для получения текущего пользователя из JWT токена.
    Используется для защищенных эндпоинтов в Swagger.
    """
    try:
        token = credentials.credentials
        payload = jwt.verify_jwt(token)

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный тип токена. Требуется access токен",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await UserRepository.find_one_or_none(
            session=session, id=int(payload.get("sub"))
        )

        return user

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

    except Exception as e:
        logger.error(f"Неожиданная ошибка в get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )


async def get_current_user_optional(
    session: AsyncDbSession,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User | None:
    """
    Dependency для опционального получения текущего пользователя из JWT токена.
    Возвращает пользователя, если токен валиден, или None, если токен отсутствует.
    """
    print(credentials)
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = jwt.verify_jwt(token)

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный тип токена. Требуется access токен",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await UserRepository.find_one_or_none(
            session=session, id=int(payload.get("sub"))
        )

        return user

    except ExpiredSignatureError:
        logger.warning("Попытка использования истёкшего токена")
    except InvalidTokenError:
        logger.warning("Попытка использования недействительного токена")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в get_current_user: {str(e)}")


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
