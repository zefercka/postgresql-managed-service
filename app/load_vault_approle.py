import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def load_approle_credentials():
    """
    Загружает AppRole credentials из файлов и устанавливает переменные окружения.

    Файлы должны быть доступны по путям:
    - /vault/approle/server-role-id (или переменная VAULT_ROLE_ID_FILE)
    - /vault/approle/server-secret-id (или переменная VAULT_SECRET_ID_FILE)
    """

    role_id_file = os.getenv("VAULT_ROLE_ID_FILE", "/vault/approle/server-role-id")
    secret_id_file = os.getenv(
        "VAULT_SECRET_ID_FILE", "/vault/approle/server-secret-id"
    )

    role_id = None
    secret_id = None

    # Читаем role_id
    try:
        role_id_path = Path(role_id_file)
        logger.info(f"Checking role_id file: {role_id_file}")

        if role_id_path.exists():
            with open(role_id_file, "r") as f:
                role_id = f.read().strip()
                if role_id:
                    os.environ["VAULT_ROLE_ID"] = role_id

                    logger.info(f"Loaded VAULT_ROLE_ID from {role_id_file}")
                else:
                    logger.info(f"AppRole role_id file is empty: {role_id_file}")
        else:
            logger.info(f"AppRole role_id file not found: {role_id_file}")
    except Exception as e:
        logger.error(f"Error reading role_id file {role_id_file}: {e}")

    # Читаем secret_id
    try:
        secret_id_path = Path(secret_id_file)
        logger.info(f"Checking secret_id file: {secret_id_file}")

        if secret_id_path.exists():
            with open(secret_id_file, "r") as f:
                secret_id = f.read().strip()
                if secret_id:
                    os.environ["VAULT_SECRET_ID"] = secret_id
                    logger.info(f"Loaded VAULT_SECRET_ID from {secret_id_file}")
                else:
                    logger.info(f"AppRole secret_id file is empty: {secret_id_file}")
        else:
            logger.info(f"AppRole secret_id file not found: {secret_id_file}")
    except Exception as e:
        logger.error(f"Error reading secret_id file {secret_id_file}: {e}")

    # Если оба credentials загружены, сбрасываем VAULT_TOKEN
    if role_id and secret_id:
        os.environ["VAULT_TOKEN"] = ""
        logger.info("Using AppRole authentication (VAULT_TOKEN cleared)")
    elif os.getenv("VAULT_TOKEN"):
        logger.info("Using token authentication (AppRole not available)")
    else:
        logger.warning("Neither AppRole nor token authentication configured!")
