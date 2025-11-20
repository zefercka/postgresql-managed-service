from fastapi import HTTPException, status


class InvalidTokenTypeError(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            detail="Неверный тип JWT: ожидался refresh токен",
        )


class InvalidRefreshTokenError(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, detail="Неверный токен обновления"
        )


class RefreshTokenExpiredError(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail="Токен обновления истёк")


class TelegramAuthError(HTTPException):
    def __init__(self, headers=None):
        super().__init__(
            status.HTTP_403_FORBIDDEN,
            "Ошибка авторизации: данные не из Telegram",
            headers,
        )


class TelegramAuthDataIsOutdatedError(HTTPException):
    def __init__(self, headers=None):
        super().__init__(
            status.HTTP_403_FORBIDDEN,
            "Ошибка авторизации: данные авторизации более неактуальны",
            headers,
        )
