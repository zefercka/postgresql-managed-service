import hashlib

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_DRIVER: str

    REPOSITORY_TYPE: str = "async"

    TELEGRAM_BOT_TOKEN: str
    # Кеш токена генерируется автоматически после инициализации
    HASH_TELEGRAM_BOT_TOKEN: str = ""

    # Время, через которое данные для входа через телеграмм становятся не актуальными
    TELEGRAM_AUTH_DATA_EXPIRE: int = 300  # 5min

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    JWT_ALGORITHM: str = "RS256"
    KEYS_PATH: str = "./keys"

    model_config = SettingsConfigDict(
        env_file=".server.env",
    )

    @property
    def SQLALCHEMY_DATABASE_URL(self):
        return (
            f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    def generate_hash_telegram_bot_token(self):
        self.HASH_TELEGRAM_BOT_TOKEN = hashlib.sha256(
            self.TELEGRAM_BOT_TOKEN.encode()
        ).digest()


settings = Config()
settings.generate_hash_telegram_bot_token()
settings.generate_hash_telegram_bot_token()
settings.generate_hash_telegram_bot_token()
