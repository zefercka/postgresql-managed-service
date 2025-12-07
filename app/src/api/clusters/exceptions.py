from fastapi import HTTPException, status

from app.src.dependency.exceptions import NotFoundError


class NotFoundClusterError(NotFoundError):
    def __init__(self, cluster_id: str):
        super().__init__(detail=f"Кластер PostgreSQL c ID '{cluster_id}' не найден")


class InvalidVersionError(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            detail="Выбранная версия PostgreSQL не поддерживается",
        )


class NoAvailableResourcesError(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_409_CONFLICT, "Нет доступных ресурсов для создания кластера"
        )


class ClusterCantBeChangedError(HTTPException):
    def __init__(self, cluster_id: str):
        super().__init__(
            status.HTTP_409_CONFLICT,
            detail=f"Кластер PostgreSQL с ID '{cluster_id}' не может быть изменён",
        )
