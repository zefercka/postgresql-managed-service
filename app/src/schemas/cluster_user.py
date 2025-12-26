from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.src.dependency.constants import PG_USERNAME_RE


class ClusterUserStatus(BaseModel):
    id: int
    status: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


ALLOWED_PERMISSIONS = {"CONNECT", "TEMPORARY", "CREATE"}


class BaseClusterUser(BaseModel):
    username: str = Field(min_length=1, max_length=64, description="Имя пользователя")
    permissions: str = Field(
        min_length=1,
        max_length=64,
        description="Список привилегий пользователя через запятую",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v:
            raise ValueError("Имя пользователя не может быть пустым")

        if v != v.lower():
            raise ValueError("Имя пользователя должно быть в нижнем регистре")

        if not PG_USERNAME_RE.match(v):
            raise ValueError(
                "Имя пользователя должно начинаться с буквы или подчёркивания "
                "и содержать только латинские буквы, цифры и символ подчёркивания"
            )

        if len(v.encode("utf-8")) > 63:
            raise ValueError(
                "Имя пользователя должно быть не длиннее 63 байт в кодировке UTF-8"
            )

        return v

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: str) -> str:
        if not v:
            raise ValueError("Список привилегий не может быть пустым")

        perms = [p.strip().upper() for p in v.split(",")]

        if any(not p for p in perms):
            raise ValueError("Привилегии не могут быть пустыми")

        # Проверяем, что все привилегии допустимы
        invalid_perms = set(perms) - ALLOWED_PERMISSIONS
        if invalid_perms:
            raise ValueError(
                f"Недопустимые привилегии: {', '.join(invalid_perms)}. "
                f"Разрешены только: {', '.join(sorted(ALLOWED_PERMISSIONS))}"
            )

        if len(perms) != len(set(perms)):
            raise ValueError("Привилегии не должны повторяться")

        return ",".join(sorted(set(perms)))


class CreateClusterUser(BaseClusterUser):
    pass


class UpdateClusterUser(BaseClusterUser):
    pass


class ClusterUser(BaseClusterUser):
    id: str
    cluster_id: str
    status_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    status: ClusterUserStatus

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class GetClusterUsersResponse(BaseModel):
    cluster_users: list[ClusterUser]
    total: int

    model_config = ConfigDict(from_attributes=True)
