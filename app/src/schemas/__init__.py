"""
Схемы валидации данных для API через PyDantic
"""

from .auth import RefreshToken, TelegramAuth, TokenResponse
from .cluster import Cluster, ClusterMinimal, CreateCluster, GetClustersResponse
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
    # HyperV hosts
    "CreateHypervHost",
    "HypervHost",
]
