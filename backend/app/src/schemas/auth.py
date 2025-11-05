from typing import Optional

from pydantic import BaseModel, Field


class RefreshToken(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


class TelegramAuth(BaseModel):
    id: int
    first_name: str = Field(min_length=1, max_length=64)
    last_name: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    photo_url: Optional[str] = Field(default=None)
    auth_date: int
    hash: str
