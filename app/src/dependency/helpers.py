from uuid import uuid4

from snowflake import SnowflakeGenerator

id_generator = SnowflakeGenerator(42)


def generate_user_id() -> int:
    user_id = next(id_generator)

    return user_id


def generate_cluster_id() -> str:
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
