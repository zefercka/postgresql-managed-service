from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseCluster(BaseModel):
    name: str = Field(min_length=3, max_length=64)
    pg_version: str = Field(max_length=64, description="Версия PostgreSQL")
    cpu: int = Field(ge=2, le=16, description="Кол-во vCPU")
    ram_mb: int = Field(ge=1024, le=32768, description="Кол-во ОЗУ в МБ")
    storage_gb: int = Field(ge=25, le=512, description="Кол-во места на диске в ГБ")


class CreateCluster(BaseCluster):
    pass


class ClusterStatus(BaseModel):
    id: int
    status: str = Field(max_length=32)
    description: Optional[str] = Field(max_length=256)

    model_config = ConfigDict(from_attributes=True)


class Cluster(BaseCluster):
    id: str
    status: ClusterStatus
    endpoint: Optional[str] = Field(description="Адрес для подключения")
    port: Optional[int] = Field(description="Порт на котором запущен PostgreSQL")
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, extra="ignore")
