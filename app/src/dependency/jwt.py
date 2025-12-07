import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from jwt import ExpiredSignatureError, InvalidTokenError

from app.config import settings

PRIVATE_KEY = serialization.load_pem_private_key(
    Path(settings.KEYS_PATH, "private_key.pem").read_text().encode(), password=None
)

PUBLIC_KEY = serialization.load_pem_public_key(
    Path(settings.KEYS_PATH, "public_key.pem").read_text().encode()
)


def generate_access_token(user_id: int, permission_level: int) -> str:
    """Генерирует access JWT для пользователя

    Args:
        user_id (int): идентификатор пользователя
        permission_level (int): уровень доступа пользователя
    Returns:
        str: access JWT
    """
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "permission_level": permission_level,
        "iat": now.timestamp(),
        "exp": (
            now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        ).timestamp(),
        "type": "access",
    }

    return jwt.encode(
        payload=payload, key=PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM
    )


def generate_refresh_token(user_id: int) -> str:
    """Генерирует refresh JWT для пользователя

    Args:
        user_id (int): идентификатор пользователя

    Returns:
        str: refresh JWT
    """
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now.timestamp(),
        "exp": (
            now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        ).timestamp(),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }

    return jwt.encode(
        payload=payload, key=PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM
    )


def verify_jwt(token: str) -> dict:
    """Проверяет JWT на подлинность и срок действия

    Args:
        token (str): токен для проверки

    Raises:
        ExpiredSignatureError: возникает если срок действия токена истёк
        InvalidTokenError: возникает если токен не подписан внутренним
        ключом или имеет не все необходимые поля

    Returns:
        dict: полезная нагрузка токена
    """
    try:
        payload = jwt.decode(
            token,
            key=PUBLIC_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return payload
    except ExpiredSignatureError:
        raise
    except InvalidTokenError:
        raise
