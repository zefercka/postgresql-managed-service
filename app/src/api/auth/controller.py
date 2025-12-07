from fastapi import APIRouter

from app.src.database import AsyncDbSession
from app.src.schemas.auth import RefreshToken, TelegramAuth, TokenResponse

from . import service

app = APIRouter(prefix="/auth")


@app.post("/login-telegram", summary="Вход через телеграмм")
async def login_via_telegram(
    session: AsyncDbSession, telegram_user: TelegramAuth
) -> TokenResponse:
    jwts = await service.login_via_telegram(session, telegram_user)
    return jwts


@app.post("/refresh", summary="Обновление токенов")
async def refresh_tokens(
    session: AsyncDbSession, refresh_token: RefreshToken
) -> TokenResponse:
    jwts = await service.refresh_tokens(session, refresh_token)
    return jwts
