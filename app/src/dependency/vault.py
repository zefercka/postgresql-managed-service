import logging
from functools import lru_cache
from typing import Any, AsyncGenerator, Dict, Optional

import hvac

from app.config import settings

logger = logging.getLogger(__name__)


class VaultClient:
    """Клиент для работы с HashiCorp Vault"""

    def __init__(
        self,
        vault_url: str,
        token: Optional[str] = None,
        namespace: Optional[str] = None,
        role_id: Optional[str] = None,
        secret_id: Optional[str] = None,
    ):
        """Инициализация клиента Vault

        Args:
            vault_url (str): URL адрес Vault сервера
            token (Optional[str], optional): Token для аутентификации.
            По умолчанию None.
            namespace (Optional[str], optional): Namespace в Vault.
            По умолчанию None.
            role_id (Optional[str], optional): AppRole Role ID для аутентификации.
            По умолчанию None.
            secret_id (Optional[str], optional): AppRole Secret ID для аутентификации.
            По умолчанию None.
        """

        self.vault_url = vault_url
        self.namespace = namespace
        self.client = hvac.Client(
            url=vault_url,
            token=token,
            namespace=namespace,
        )

        # Если предоставлены role_id и secret_id, используем AppRole аутентификацию
        if role_id and secret_id:
            self._authenticate_with_approle(role_id, secret_id)

    def is_authenticated(self) -> bool:
        """Проверка аутентификации клиента."""
        try:
            return self.client.is_authenticated()
        except Exception as e:
            logger.error(f"Ошибка при проверке аутентификации: {e}")
            return False

    def _authenticate_with_approle(self, role_id: str, secret_id: str) -> bool:
        """Аутентификация с использованием AppRole.

        Args:
            role_id (str): AppRole Role ID
            secret_id (str): AppRole Secret ID

        Returns:
            bool: True если аутентификация успешна, False иначе
        """
        try:
            response = self.client.auth.approle.login(
                role_id=role_id,
                secret_id=secret_id,
            )

            # Устанавливаем полученный токен
            token = response.get("auth", {}).get("client_token")
            if token:
                self.client.token = token
                logger.info("Успешная аутентификация через AppRole")
                return True
            else:
                logger.error("Не удалось получить токен из ответа AppRole")
                return False

        except Exception as e:
            logger.error(f"Ошибка при аутентификации через AppRole: {e}")
            return False

    def read_secret(
        self,
        path: str,
        mount_point: str = "secret",
        version: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Чтение секрета из KV v2.

        Args:
            path (str): Путь до секрета
            mount_point (str, optional): Точка монтирования секретов.
            По умолчанию 'secret'.
            version (Optional[int], optional): Версия секрета (для KV v2).
            По умолчанию None.

        Returns:
            Optional[Dict[str, Any]]: Данные секрета или None в случае ошибки
        """

        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point,
                version=version,
            )
            return response.get("data", {}).get("data")
        except Exception as e:
            logger.error(f"Ошибка при чтении секрета {path}: {e}")
            return None

    def write_secret(
        self,
        path: str,
        secret: Dict[str, Any],
        mount_point: str = "secret",
        cas: Optional[int] = None,
    ) -> bool:
        """Запись секрета в KV v2

        Args:
            path (str): Путь до секрета
            secret (Dict[str, Any]): Данные секрета
            mount_point (str, optional): Точка монтирования секретов.
            По умолчанию "secret".
            cas (Optional[int], optional): Check-And-Set параметр для
            версионирования. По умолчанию None.

        Returns:
            bool: True если запись успешна, False иначе
        """

        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret,
                mount_point=mount_point,
                cas=cas,
            )
            logger.info(f"Секрет успешно записан: {path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при записи секрета {path}: {e}")
            return False

    def delete_secret(
        self,
        path: str,
        mount_point: str = "secret",
    ) -> bool:
        """Удаление последней версии секрета.

        Args:
            path (str): Путь до секрета
            mount_point (str, optional): Точка монтирования секретов.
            По умолчанию "secret".

        Returns:
            bool: True если удаление успешно, False иначе
        """

        try:
            self.client.secrets.kv.v2.delete_latest_version_of_secret(
                path=path,
                mount_point=mount_point,
            )
            logger.info(f"Секрет успешно удален: {path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении секрета {path}: {e}")
            return False

    def list_secrets(
        self,
        path: str = "",
        mount_point: str = "secret",
    ) -> Optional[list]:
        """Получение списка секретов по указанному пути.

        Args:
            path (str, optional): Путь для просмотра. По умолчанию "".
            mount_point (str, optional): Точка монтирования секретов.
            По умолчанию "secret".

        Returns:
            Optional[list]: Список ключей секретов или None в случае ошибки
        """

        try:
            response: dict = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=mount_point,
            )
            return response.get("data", {}).get("keys", [])
        except Exception as e:
            logger.error(f"Ошибка при получении списка секретов {path}: {e}")
            return None

    def read_secret_metadata(
        self,
        path: str,
        mount_point: str = "secret",
    ) -> Optional[Dict[str, Any]]:
        """
        Чтение метаданных секрета.

        Args:
            path (str): Путь до секрета
            mount_point (str, optional): Точка монтирования секретов.
            По умолчанию "secret".

        Returns:
            Optional[Dict[str, Any]]: Метаданные секрета или None в
            случае ошибки
        """
        try:
            response: dict = self.client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point=mount_point,
            )
            return response.get("data")
        except Exception as e:
            logger.error(f"Ошибка при чтении метаданных секрета {path}: {e}")
            return None

    def destroy_secret_versions(
        self,
        path: str,
        versions: list[int],
        mount_point: str = "secret",
    ) -> bool:
        """
        Уничтожение конкретных версий секрета (безвозвратно).

        Args:
            path: Путь до секрета
            versions: Список версий для уничтожения
            mount_point: Точка монтирования секретов

        Returns:
            True если уничтожение успешно, False иначе
        """
        try:
            self.client.secrets.kv.v2.destroy_secret_versions(
                path=path,
                versions=versions,
                mount_point=mount_point,
            )
            logger.info(f"Версии {versions} секрета {path} уничтожены")
            return True
        except Exception as e:
            logger.error(f"Ошибка при уничтожении версий секрета {path}: {e}")
            return False


@lru_cache()
def get_vault_client() -> VaultClient:
    """Получение singleton экземпляра VaultClient.

    Returns:
        VaultClient: Экземпляр VaultClient
    """

    vault_url = settings.VAULT_ADDR
    vault_token = settings.VAULT_TOKEN if settings.VAULT_TOKEN else None

    # Проверяем, используется ли AppRole аутентификация
    role_id = getattr(settings, "VAULT_ROLE_ID", None)
    secret_id = getattr(settings, "VAULT_SECRET_ID", None)

    client = VaultClient(
        vault_url=vault_url,
        token=vault_token,
        role_id=role_id,
        secret_id=secret_id,
    )

    if not client.is_authenticated():
        logger.warning("Vault клиент не аутентифицирован!")

    return client


# Dependency для FastAPI
async def get_vault_dependency() -> AsyncGenerator[VaultClient, None]:
    """FastAPI dependency для получения Vault клиента.

    Returns:
        AsyncGenerator[VaultClient, None]: VaultClient instance

    Yields:
        Iterator[AsyncGenerator[VaultClient, None]]: VaultClient instance
    """

    yield get_vault_client()
