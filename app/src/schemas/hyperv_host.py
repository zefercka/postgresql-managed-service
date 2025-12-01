from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseHypervHost(BaseModel):
    host_fqdn: str = Field(description="Адрес хоста")
    winrm_port: int = Field(description="Порт на котором работает WinRM")
    https: bool = Field(description="Использовать ли https при подключении")
    location: Optional[str] = Field(default=None, description="Локация сервера")
    description: Optional[str] = Field(default=None, description="Описание сервера")
    total_storage: int = Field(ge=0, description="Общий объем хранилища в ГБ")
    total_ram: int = Field(ge=0, description="Общий объем оперативной памяти в МБ")
    total_cpu: int = Field(ge=0, description="Общее кол-во ядер процессора")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CreateHypervHost(BaseHypervHost):
    pass


class HypervHostStatus(BaseModel):
    id: int
    status: str
    description: Optional[str] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class HypervHost(BaseHypervHost):
    id: int
    status: HypervHostStatus
    free_storage: int = Field(ge=0, description="Свободный объем хранилища в ГБ")
    free_ram: int = Field(ge=0, description="Свободный объем оперативной памяти в МБ")
    free_cpu: int = Field(ge=0, description="Свободное кол-во ядер процессора")
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class HypervHostResponse(BaseModel):
    hosts: list[HypervHost]
    total: int = Field(description="Всего HyperV хостов")

    model_config = ConfigDict(from_attributes=True)


class HypervHostAudit(BaseModel):
    id: int
    user_id: int
    hyperv_host_id: int
    log: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
