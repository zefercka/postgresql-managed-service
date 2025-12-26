from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.src.dependency.constants import DB_NAME_RE


class DBNameValidator:
    @field_validator("db_name")
    @classmethod
    def validate_db_name(cls, v: str) -> str:
        if not v:
            raise ValueError("Название БД не может быть пустым")

        if v != v.lower():
            raise ValueError("Название БД должно быть в нижнем регистре")

        if not DB_NAME_RE.match(v):
            raise ValueError(
                "Имя базы данных должно начинаться с буквы или подчёркивания "
                "и содержать только латинские буквы, цифры и символ подчёркивания"
            )

        if len(v.encode("utf-8")) > 63:
            raise ValueError(
                "Имя базы данных должно быть не длиннее 63 байт в кодировке UTF-8"
            )

        return v


class BaseCluster(BaseModel):
    name: str = Field(min_length=3, max_length=64)
    cpu: int = Field(ge=2, le=16, description="Кол-во vCPU")
    ram_mb: int = Field(ge=1024, le=32768, description="Кол-во ОЗУ в МБ")
    storage_gb: int = Field(ge=10, le=512, description="Кол-во места на диске в ГБ")


class CreateCluster(BaseCluster, DBNameValidator):
    db_name: str = Field(min_length=1, max_length=64, description="Название БД")
    pg_version: str = Field(max_length=64, description="Версия PostgreSQL")


class UpdateCluster(BaseCluster):
    pass


class ClusterStatus(BaseModel):
    id: int
    status: str = Field(max_length=32)
    description: Optional[str] = Field(max_length=256)

    model_config = ConfigDict(from_attributes=True)


class ClusterMinimal(BaseCluster):
    id: str
    status: ClusterStatus
    pg_version: str = Field(max_length=64, description="Версия PostgreSQL")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class Cluster(BaseCluster, DBNameValidator):
    id: str
    status: ClusterStatus
    pg_version: str = Field(max_length=64, description="Версия PostgreSQL")
    db_name: str = Field(min_length=1, max_length=63, description="Название БД")
    connection_string: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    host_fqdn: Optional[str] = Field(default=None)
    postgres_port: Optional[int] = Field(default=None, serialization_alias="port")
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    @model_validator(mode="after")
    def generate_connect_string(self):
        if all(
            [
                self.username,
                self.host_fqdn,
                self.postgres_port,
                self.name,
                self.password,
            ]
        ):
            self.connection_string = (
                f"{self.username}@{self.host_fqdn}:{self.postgres_port}/{self.name}"
            )

        return self


class GetClustersResponse(BaseModel):
    clusters: list[ClusterMinimal]
    total: int = Field(description="Всего кластеров у пользователя")

    model_config = ConfigDict(from_attributes=True)
