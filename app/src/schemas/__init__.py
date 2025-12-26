"""
Схемы валидации данных для API через PyDantic
"""

from .auth import RefreshToken, TelegramAuth, TokenResponse
from .backup import (
    BackupListResponse,
    BackupResponse,
    BackupStatus,
    BackupType,
    CreateBackup,
    UpdateBackup,
)
from .cluster import (
    Cluster,
    ClusterMinimal,
    CreateCluster,
    GetClustersResponse,
    UpdateCluster,
)
from .cluster_user import (
    ClusterUser,
    CreateClusterUser,
    GetClusterUsersResponse,
    UpdateClusterUser,
)
from .hyperv_host import CreateHypervHost, HypervHost

__all__ = [
    # Auth
    "RefreshToken",
    "TelegramAuth",
    "TokenResponse",
    # Cluster
    "Cluster",
    "ClusterMinimal",
    "CreateCluster",
    "GetClustersResponse",
    "UpdateCluster",
    # ClusterUser
    "ClusterUser",
    "CreateClusterUser",
    "GetClusterUsersResponse",
    "UpdateClusterUser",
    # HyperV hosts
    "CreateHypervHost",
    "HypervHost",
]
