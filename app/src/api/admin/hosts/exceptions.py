from app.src.dependency.exceptions import ConflictError, NotFoundError


class HostAlreadyExistsError(ConflictError):
    def __init__(self):
        super().__init__(detail="HyperV хост с таким адресом уже существует")


class NotFoundHostError(NotFoundError):
    def __init__(self):
        super().__init__(detail="HyperV хост не найден")


class HostCantBeChangedError(ConflictError):
    def __init__(self):
        super().__init__(
            detail="Новые параметры HyperV хоста не могут быть применены, т.к. нарушают его состояние"
        )


class HostCantBeDeletedError(ConflictError):
    def __init__(self):
        super().__init__(
            detail="На этом HyperV хосте ещё остались кластеры. Перенести их, чтобы удалить хост"
        )
