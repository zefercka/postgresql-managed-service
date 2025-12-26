import hashlib
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.load_vault_approle import load_approle_credentials

load_approle_credentials()


class Config(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_DRIVER: str

    REPOSITORY_TYPE: str = "async"

    TELEGRAM_AUTH_ENABLED: bool = True

    TELEGRAM_BOT_TOKEN: str
    # Кеш токена генерируется автоматически после инициализации
    HASH_TELEGRAM_BOT_TOKEN: str = ""

    # Время, через которое данные для входа через телеграмм становятся
    # не актуальными
    TELEGRAM_AUTH_DATA_EXPIRE: int = 300  # 5min

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    JWT_ALGORITHM: str = "RS256"
    KEYS_PATH: str = "./keys/jwt"

    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_VHOST: str

    TERRAFORM_DIR: str

    VM_SOURCE_DISK_PATH: str

    # Путь до приватного ключами для подключения по SSH к серверам
    SERVERS_KEY_PATH: str = "./keys/servers/ssh_key"

    # HashiCorp Vault
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: str = ""
    VAULT_NAMESPACE: str = ""

    # AppRole authentication (альтернатива токену)
    VAULT_ROLE_ID: str = ""
    VAULT_SECRET_ID: str = ""

    VAULT_CLUSTERS_SECRET_PATH: str = "secrets/clusters"

    ANSIBLE_SSH_PRIVATE_KEY_PATH: str = "./keys/ansible/ssh_key"

    model_config = SettingsConfigDict(
        env_file=".server.env",
    )

    @property
    def SQLALCHEMY_DATABASE_URL(self):
        return (
            f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def RABBITMQ_CONNECTION_URL(self):
        return (
            "amqp://"
            f"{self.RABBITMQ_DEFAULT_USER}:{self.RABBITMQ_DEFAULT_PASS}@"
            f"{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
        )

    @property
    def TERRAFORM_DIR_FULL_PATH(self):
        return Path(self.TERRAFORM_DIR).resolve()

    def generate_hash_telegram_bot_token(self):
        self.HASH_TELEGRAM_BOT_TOKEN = hashlib.sha256(
            self.TELEGRAM_BOT_TOKEN.encode()
        ).digest()


settings = Config()
settings.generate_hash_telegram_bot_token()
