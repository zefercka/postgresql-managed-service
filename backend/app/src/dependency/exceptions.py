from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(
        self, status_code: int = status.HTTP_404_NOT_FOUND, detail=None, headers=None
    ):
        super().__init__(status_code, detail, headers)


class NoPermissionsError(HTTPException):
    def __init__(
        self, status_code: int = status.HTTP_403_FORBIDDEN, detail=None, headers=None
    ):
        super().__init__(status_code, detail, headers)


class LimitExceededError(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_429_TOO_MANY_REQUESTS,
        detail=None,
        headers=None,
    ):
        super().__init__(status_code, detail, headers)


class ConflictError(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_409_CONFLICT,
        detail=None,
        headers=None,
    ):
        super().__init__(status_code, detail, headers)


class InternalError(HTTPException):
    def __init__(self, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code, detail="Произошла внутренняя ошибка")


class UnknownAuthorizationTypeError(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            detail="Неизвестный тип авторизации",
        )
