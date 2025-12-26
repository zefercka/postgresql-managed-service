import secrets
import string
from uuid import uuid4

from snowflake import SnowflakeGenerator

id_generator = SnowflakeGenerator(42)


def generate_user_id() -> int:
    user_id = next(id_generator)

    return user_id


def generate_uuid_id() -> str:
    cluster_id = uuid4()

    return str(cluster_id)


def generate_audit_log(old_values: dict, new_values: dict) -> str | None:
    """Генерирует текстовый лог изменения значений. Возвращает None если
    изменений не было
    """

    old_values.pop("updated_at", None)
    new_values.pop("updated_at", None)

    lines = []
    all_keys = set(old_values.keys()) | set(new_values.keys())

    for key in sorted(all_keys):
        old_val = old_values.get(key, "<отсутствовал>")
        new_val = new_values.get(key, "<удалён>")
        if old_val == new_val:
            continue
        lines.append(f"{key}: {old_val} → {new_val}")

    if not lines:
        return None

    return "\n".join(lines)


def generate_postgres_password(length: int = 12) -> str:
    """Генерирует пароль для пользователя PostgreSQL заданной длины

    Args:
        length (int, optional): Длина пароля. По умолчанию 12.

    Returns:
        str: Пароль
    """

    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = string.punctuation

    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]

    all_chars = lowercase + uppercase + digits + symbols
    password += [secrets.choice(all_chars) for _ in range(length - len(password))]

    secrets.SystemRandom().shuffle(password)

    return "".join(password)


def generate_postgres_username(length: int = 6) -> str:
    """Генерирует имя пользователя заданной длины для пользователя
    PostgreSQL

    Args:
        length (int, optional): Длина имени. По умолчанию 6.

    Returns:
        str: Имя пользователя
    """

    username = [secrets.choice(string.ascii_lowercase) for _ in range(length)]

    secrets.SystemRandom().shuffle(username)

    return "".join(username)
