from fastapi import HTTPException, status

from app.src.dependency.exceptions import NotFoundError


class NotFoundClusterUserError(NotFoundError):
    def __init__(self, cluster_user_id: str):
        super().__init__(
            detail=f"Пользователь кластера с ID '{cluster_user_id}' не найден"
        )


class ClusterUserAlreadyExistsError(HTTPException):
    def __init__(self, username: str):
        super().__init__(
            status.HTTP_409_CONFLICT,
            detail=f"Пользователь с именем '{username}' уже существует",
        )
