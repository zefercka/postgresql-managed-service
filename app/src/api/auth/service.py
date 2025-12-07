import hashlib
import hmac
import time

from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.src.database.repository import UserRepository
from app.src.dependency import helpers, jwt
from app.src.schemas.auth import RefreshToken, TelegramAuth, TokenResponse

from .exceptions import (
    InvalidRefreshTokenError,
    InvalidTokenTypeError,
    RefreshTokenExpiredError,
    TelegramAuthDataIsOutdatedError,
    TelegramAuthError,
)


async def login_via_telegram(
    session: AsyncSession, telegram_user: TelegramAuth
) -> TokenResponse:
    """
    Выполняет авторизацию пользователя через телеграмм
    """
    data = telegram_user.model_dump(exclude=["hash"])
    sorted_keys = sorted(data.keys())
    data_check_arr = [
        f"{key}={data[key]}" for key in sorted_keys if data[key] is not None
    ]
    data_check = "\n".join(data_check_arr)

    computed_hash = hmac.new(
        settings.HASH_TELEGRAM_BOT_TOKEN, data_check.encode(), hashlib.sha256
    ).hexdigest()

    if (
        not hmac.compare_digest(computed_hash, telegram_user.hash)
        and telegram_user.id != 0
    ):
        raise TelegramAuthError

    if time.time() - telegram_user.auth_date > settings.TELEGRAM_AUTH_DATA_EXPIRE:
        raise TelegramAuthDataIsOutdatedError

    db_user = await UserRepository.find_one_or_none(session, tg_id=telegram_user.id)
    if db_user is None:
        data = telegram_user.model_dump(
            include=["id", "first_name", "last_name", "username"]
        )
        data["tg_id"] = data.pop("id")
        data["id"] = helpers.generate_user_id()

        db_user = await UserRepository.add(session, **data)

    access_token = jwt.generate_access_token(db_user.id, db_user.permission_level)
    refresh_token = jwt.generate_refresh_token(db_user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_tokens(
    session: AsyncSession, refresh_token: RefreshToken
) -> TokenResponse:
    """
    Обновляет access и refresh токены используя валидный refresh токен
    из тела запроса
    """
    token = refresh_token.refresh_token

    try:
        payload = jwt.verify_jwt(token)
    except InvalidTokenError:
        raise InvalidRefreshTokenError from None
    except ExpiredSignatureError:
        raise RefreshTokenExpiredError from None

    if payload.get("type") != "refresh":
        raise InvalidTokenTypeError

    user_id = payload.get("sub")

    user = await UserRepository.find_one_or_none(session, id=int(user_id))
    if user is None:
        raise InvalidRefreshTokenError

    access_token = jwt.generate_access_token(user_id, user.permission_level)
    refresh_token = jwt.generate_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
