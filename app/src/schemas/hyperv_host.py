import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    disks_path: str = Field(description="Путь для хранения дисков ВМ")

    @field_validator("disks_path")
    @classmethod
    def validate_disks_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Путь для хранения дисков не может быть пустым")

        # Проверка на корректность Windows пути
        windows_path_pattern = r"^([a-zA-Z]:\\|\\\\)[\w\s\-\\.\\]+$"
        if not re.match(windows_path_pattern, v):
            raise ValueError(
                "Путь должен быть корректным Windows путем (например, C:\\VMs или \\\\server\\share\\VMs)"
            )

        if not (v.startswith("\\\\") or (len(v) > 2 and v[1] == ":")):
            raise ValueError("Путь должен быть абсолютным")

        return v.strip()


class UpdateHypervHost(BaseHypervHost):
    pass


class HypervHostStatus(BaseModel):
    id: int
    status: str
    description: Optional[str] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class HypervHost(BaseHypervHost):
    id: int
    status: HypervHostStatus
    disks_path: str = Field(description="Путь для хранения дисков ВМ")
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
