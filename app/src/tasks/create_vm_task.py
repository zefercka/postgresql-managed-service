import json
import logging
import os
import shutil
import subprocess
from typing import Any

import dramatiq

from app.config import settings
from app.src.database import get_db
from app.src.database.declarations.cluster import ClusterStatusEnum
from app.src.database.repository.synchronous import (
    ClusterRepository,
    HypervHostRepository,
)

from .worker import rabbitmq_broker  # noqa: F401

logger = logging.getLogger(__name__)

MAX_RETRIES = 5


@dramatiq.actor(max_retries=MAX_RETRIES, queue_name="terraform_queue")
def create_vm_task(cluster_id: str):
    """
    Задача создания новой виртуальной машины
    """

    with get_db() as session:
        cluster = ClusterRepository.find_one_or_none(session, id=cluster_id)
        host = HypervHostRepository.find_one_or_none(session, id=cluster.hyperv_host_id)

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
    }

    write_configuration(cluster_id, vm_config, host_config)

    vm_ip, ssh_port, postgres_port = run_terraform_apply(
        cwd=str(settings.TERRAFORM_DIR_FULL_PATH / str(host_config["id"]))
    )

    with get_db() as session:
        ClusterRepository.update(
            session,
            cluster_id,
            postgres_port=postgres_port,
            ssh_port=ssh_port,
            host_fqdn=vm_ip,
        )

    logger.info(f"VM for cluster '{cluster_id}' was created")


def create_host_dir_if_not_exists(host_id: int):
    """Проверяет существует ли папка для хоста и если нет, то создает ее
    и копирует туда шаблонные файлы.
    """
    host_directories = set(os.listdir(str(settings.TERRAFORM_DIR_FULL_PATH)))

    if str(host_id) not in host_directories:
        os.mkdir(str(settings.TERRAFORM_DIR_FULL_PATH / str(host_id)))

        src = settings.TERRAFORM_DIR_FULL_PATH / "template"
        dst = settings.TERRAFORM_DIR_FULL_PATH / str(host_id)

        shutil.copytree(src, dst, dirs_exist_ok=True)


def write_configuration(
    cluster_id: str,
    vm_config: dict[str, Any],
    host_config: dict[str, Any] | None = None,
):
    """Записывает конфигурацию виртуальной машины и хоста в файл
    terraform.tfvars.json для нужного хоста. Создаёт файл если ещё не
    существует.
    """
    open_mode = "r+"
    path = (
        settings.TERRAFORM_DIR_FULL_PATH
        / str(host_config["id"])
        / "terraform.tfvars.json"
    )
    if not os.path.exists(str(path)):
        open_mode = "w+"

    with open(path, open_mode) as f:
        content = f.read()

        if content:
            tfvars = json.loads(content)
        else:
            tfvars = {}

        tfvars["hyperv_host"] = host_config

        if tfvars.get("vms") is None:
            tfvars["vms"] = {cluster_id: vm_config}
        else:
            tfvars["vms"][cluster_id] = vm_config

        f.seek(0)
        f.write(json.dumps(tfvars))
        f.truncate()


def run_terraform_apply(cwd: str) -> tuple[str, int, int]:
    """Выполняет команды terraform init и terraform apply и возвращает
    ip, ssh_port и postgres_port для созданной ВМ
    """

    subprocess.run(["terraform", "init"], cwd=cwd, check=True)

    subprocess.run(
        ["terraform", "apply", "-auto-approve", "-parallelism", "1"],
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

    vm_ip = outputs["vm_ip"]["value"]
    ssh_port = outputs["ssh_port"]["value"]
    postgres_port = outputs["postgres_port"]["value"]

    print(type(vm_ip), type(ssh_port), type(postgres_port))

    return vm_ip, ssh_port, postgres_port


@dramatiq.actor()
def rollback_tfvars_file(message_data, exception_data):
    logger.error(exception_data)

    if message_data["options"]["retries"] == MAX_RETRIES:
        cluster_id = message_data["args"][0]

        try:
            with get_db() as session:
                cluster = ClusterRepository.find_one_or_none(session, id=cluster_id)

                host_id = cluster.hyperv_host_id

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
                HypervHostRepository.update(
                    session,
                    id=host_id,
                    free_storage=host.free_storage + cluster.storage_gb,
                    free_ram=host.free_ram + cluster.ram_mb,
                    free_cpu=host.free_cpu + cluster.cpu,
                )
        except Exception as err:
            logger.error(err)

        open_mode = "r+"
        path = settings.TERRAFORM_DIR_FULL_PATH / str(host_id) / "terraform.tfvars.json"
        if not os.path.exists(str(path)):
            open_mode = "w+"

        with open(path, open_mode) as f:
            content = f.read()
            if not content:
                logger.warning(f"Empty file {path}")
                return

            if content:
                tfvars = json.loads(content)

            if tfvars.get("vms") is None:
                logger.warning(f"Not 'vms' key in {path}")
                return
            else:
                tfvars["vms"].pop(cluster_id)

            f.seek(0)
            f.write(json.dumps(tfvars))
            f.truncate()

    print(message_data["options"])
    print(message_data["options"]["retries"])
    print(exception_data)
