import json
import logging
import shutil
import subprocess
from typing import Any

import dramatiq
from filelock import FileLock

from app.config import settings
from app.src.database import get_db
from app.src.database.declarations.cluster import ClusterStatusEnum
from app.src.database.repository.synchronous import (
    ClusterRepository,
    HypervHostRepository,
)
from app.src.dependency import helpers, vault

from .worker import rabbitmq_broker  # noqa: F401

logger = logging.getLogger(__name__)

MAX_RETRIES = 5


@dramatiq.actor(max_retries=MAX_RETRIES, queue_name="terraform_queue")
def create_vm_task(cluster_id: str):
    """
    Задача создания новой виртуальной машины
    """
    try:
        with get_db() as session:
            cluster = ClusterRepository.find_one_or_none(session, id=cluster_id)
            if not cluster:
                raise ValueError(f"Cluster {cluster_id} not found")

            host = HypervHostRepository.find_one_or_none(
                session, id=cluster.hyperv_host_id
            )
            if not host:
                raise ValueError(f"Host for cluster {cluster_id} not found")

        create_super_user_creds(cluster_id)
        create_host_dir_if_not_exists(host.id)

        host_config = {
            "id": host.id,
            "host": host.host_fqdn,
            "port": host.winrm_port,
            "https": host.https,
            "disks_path": host.disks_path,
        }

        vm_config = {
            "cpu": cluster.cpu,
            "memory": cluster.ram_mb,
            "disk_size": cluster.storage_gb,
            "source_disk_path": str(settings.VM_SOURCE_DISK_PATH),
            "host": host.id,
            "pg_version": cluster.pg_version,
            "db_name": cluster.db_name,
        }

        write_configuration(cluster_id, vm_config, host_config)

        terraform_lock_path = (
            settings.TERRAFORM_DIR_FULL_PATH / str(host_config["id"]) / "terraform.lock"
        )

        with FileLock(terraform_lock_path, timeout=1800):
            clusters_info = run_terraform_apply(
                cwd=str(settings.TERRAFORM_DIR_FULL_PATH / str(host_config["id"]))
            )

        cluster_info = clusters_info[cluster_id]

        with get_db() as session:
            ClusterRepository.update(
                session,
                cluster_id,
                status_id=ClusterStatusEnum.RUNNING,
                postgres_port=cluster_info["postgres_port"],
                ssh_port=cluster_info["ssh_port"],
                host_fqdn=cluster_info["ip"],
            )

        logger.info(f"VM for cluster '{cluster_id}' was created")

    except Exception as err:
        logger.exception("Create VM task failed")
        raise err


def create_host_dir_if_not_exists(host_id: int):
    host_dir = settings.TERRAFORM_DIR_FULL_PATH / str(host_id)
    if not host_dir.exists():
        host_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            settings.TERRAFORM_DIR_FULL_PATH / "template",
            host_dir,
            dirs_exist_ok=True,
        )


def write_configuration(
    cluster_id: str,
    vm_config: dict[str, Any],
    host_config: dict[str, Any],
):
    """Записывает конфигурацию виртуальной машины и хоста в файл
    terraform.tfvars.json для нужного хоста. Создаёт файл если ещё не
    существует.
    """

    path = (
        settings.TERRAFORM_DIR_FULL_PATH
        / str(host_config["id"])
        / "terraform.tfvars.json"
    )
    lock_path = path.with_suffix(".json.lock")

    with FileLock(lock_path, timeout=300):
        if path.exists():
            content = path.read_text()
            tfvars = json.loads(content) if content else {}
        else:
            tfvars = {}

        tfvars["hyperv_host"] = host_config
        tfvars.setdefault("vms", {})
        tfvars["vms"][cluster_id] = vm_config

        path.write_text(json.dumps(tfvars, indent=2))


def run_terraform_apply(cwd: str) -> dict[str, dict[str, Any]]:
    subprocess.run(["terraform", "init"], cwd=cwd, check=True)
    subprocess.run(
        ["terraform", "apply", "-auto-approve"],
        cwd=cwd,
        check=True,
    )

    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )

    outputs = json.loads(result.stdout)
    vm_configs = outputs["vm_configs"]["value"]

    vm_info: dict[str, dict[str, Any]] = {}

    for cluster_id, data in vm_configs.items():
        vm_info[cluster_id] = {
            "ip": data["ip"]["value"],
            "ssh_port": data["ssh_port"]["value"],
            "postgres_port": data["postgres_port"]["value"],
        }

    return vm_info


@dramatiq.actor()
def rollback_tfvars_file(message_data, exception_data):
    logger.error("ROLLBACK STARTED")
    logger.error("Exception: %s", exception_data)
    logger.error("Message data: %s", message_data)

    retries = message_data.get("options", {}).get("retries", 0)
    if retries < MAX_RETRIES:
        return

    cluster_id = message_data["args"][0]

    with get_db() as session:
        cluster = ClusterRepository.find_one_or_none(session, id=cluster_id)
        if not cluster:
            logger.error("Cluster not found during rollback")
            return

        host_id = cluster.hyperv_host_id
        if not host_id:
            logger.error("host_id is None, rollback aborted")
            return

        ClusterRepository.update(
            session,
            cluster_id,
            status_id=ClusterStatusEnum.FAILED,
            hyperv_host_id=None,
            postgres_port=None,
            ssh_port=None,
            host_fqdn=None,
        )

        host = HypervHostRepository.find_one_or_none(session, id=host_id)
        if host:
            HypervHostRepository.update(
                session,
                id=host_id,
                free_storage=host.free_storage + cluster.storage_gb,
                free_ram=host.free_ram + cluster.ram_mb,
                free_cpu=host.free_cpu + cluster.cpu,
            )

    path = settings.TERRAFORM_DIR_FULL_PATH / str(host_id) / "terraform.tfvars.json"
    lock_path = path.with_suffix(".json.lock")

    if not path.exists():
        logger.warning("tfvars file does not exist: %s", path)
        return

    with FileLock(lock_path, timeout=300):
        content = path.read_text()
        if not content:
            logger.warning("Empty tfvars file: %s", path)
            return

        tfvars = json.loads(content)
        vms = tfvars.get("vms", {})

        if cluster_id in vms:
            vms.pop(cluster_id)
            path.write_text(json.dumps(tfvars, indent=2))
            logger.info("Cluster %s removed from tfvars", cluster_id)
        else:
            logger.warning("Cluster %s not found in tfvars", cluster_id)


def create_super_user_creds(cluster_id: str):
    username = helpers.generate_postgres_username()
    password = helpers.generate_postgres_password()

    client = vault.get_vault_client()
    status = client.write_secret(
        path=f"{cluster_id}/users/super",
        secret={"username": username, "password": password},
        mount_point="clusters",
    )

    if not status:
        raise RuntimeError("Couldn't create vault secret for super user")
