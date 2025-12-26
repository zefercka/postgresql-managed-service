from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BackupStatus(BaseModel):
    id: int
    status: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BackupType(BaseModel):
    id: int
    type: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BaseBackup(BaseModel):
    name: str = Field(min_length=1, max_length=128, description="Название бекапа")


class CreateBackup(BaseBackup):
    cluster_id: str = Field(description="Идентификатор кластера")
    type_id: Optional[int] = Field(
        default=0, description="Тип бекапа (0 - manual, 1 - scheduled)"
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="Дата истечения срока хранения"
    )


class UpdateBackup(BaseModel):
    name: Optional[str] = Field(
        default=None, min_length=1, max_length=128, description="Название бекапа"
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="Дата истечения срока хранения"
    )


class BackupResponse(BaseBackup):
    id: str
    cluster_id: str
    status_id: int
    type_id: int
    s3_bucket: str
    s3_key: str
    s3_region: Optional[str] = None
    size_bytes: Optional[int] = None
    pg_version: str
    compression: Optional[str] = None
    backup_method: Optional[str] = None
    error_message: Optional[str] = None
    created_by: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    status: BackupStatus
    type: BackupType

    model_config = ConfigDict(from_attributes=True)


class BackupListResponse(BaseModel):
    backups: list[BackupResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
