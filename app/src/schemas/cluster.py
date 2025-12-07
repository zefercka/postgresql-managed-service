from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BaseCluster(BaseModel):
    name: str = Field(min_length=3, max_length=64)
    cpu: int = Field(ge=2, le=16, description="Кол-во vCPU")
    ram_mb: int = Field(ge=1024, le=32768, description="Кол-во ОЗУ в МБ")
    storage_gb: int = Field(ge=10, le=512, description="Кол-во места на диске в ГБ")


class CreateCluster(BaseCluster):
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


class Cluster(BaseCluster):
    id: str
    status: ClusterStatus
    pg_version: str = Field(max_length=64, description="Версия PostgreSQL")
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
