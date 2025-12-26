import logging
import subprocess

import dramatiq

from app.config import settings
from app.src.database import get_db
from app.src.database.repository.synchronous import (
    ClusterRepository,
    ClusterUserRepository,
    HypervHostRepository,
)
from app.src.dependency import helpers, vault

from .worker import rabbitmq_broker  # noqa: F401

logger = logging.getLogger(__name__)

MAX_RETRIES = 5


@dramatiq.actor(max_retries=MAX_RETRIES, queue_name="ansible_queue")
def create_cluster_user_task(cluster_user_id):
    """
    Задача создания пользователя кластера PostgreSQL
    """
    try:
        with get_db() as session:
            cluster_user = ClusterUserRepository.find_one_or_none(
                session, id=cluster_user_id
            )
            if not cluster_user:
                raise ValueError(f"Cluster user {cluster_user_id} not found")

            cluster = ClusterRepository.find_one_or_none(
                session, id=cluster_user.cluster_id
            )
            if not cluster:
                raise ValueError(f"Cluster {cluster_user.cluster_id} not found")

            host = HypervHostRepository.find_one_or_none(
                session, id=cluster.hyperv_host_id
            )
            if not host:
                raise ValueError(f"Host for cluster {cluster.id} not found")

        password = helpers.generate_postgres_password()

        client = vault.get_vault_client()
        client.write_secret(
            path=f"{cluster.id}/users/{cluster_user.username}",
            secret={"password": password},
            mount_point="clusters",
        )

        cmd = (
            f"ansible-playbook /opt/postgresql-managed-service/ansible/action_db_user.yaml "
            f"-e user_name='{cluster_user.username}' "
            f"-e password='{password}' "
            "-e grant=present "
            "-e privs=CONNECT "
            f"-e db_name='{cluster.db_name}' "
            "-e present=present "
            f"-e ansible_port={cluster.ssh_port} "
            "-u automation "
            f"--private-key={settings.ANSIBLE_SSH_PRIVATE_KEY_PATH} "
            f"-i {host.host_fqdn}, "
        )

        subprocess.run([cmd], check=True)

    except Exception as e:
        logger.error(f"Error creating cluster user {cluster_user_id}: {e}")
        raise
