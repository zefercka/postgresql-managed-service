from uuid import uuid4

from snowflake import SnowflakeGenerator

id_generator = SnowflakeGenerator(42)


def generate_user_id() -> int:
    user_id = next(id_generator)

    return user_id


def generate_cluster_id() -> str:
    cluster_id = uuid4()

    return str(cluster_id)
