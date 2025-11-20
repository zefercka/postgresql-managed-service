import dramatiq
from app.src.database import get_db
from app.src.database.repository.synchronous import ClusterRepository
from app.src.database.declarations import ClusterStatusEnum

import json
import subprocess

from .worker import rabbitmq_broker  # noqa: F401
from app.config import settings

import yaml
import paramiko


@dramatiq.actor(max_retries=5)
def create_vm_task(cluster_id: str):
    """
    Задача создания новой виртуальной машины
    """

    print(cluster_id)

    with get_db() as session:
        cluster = ClusterRepository.find_one_or_none(session, id=cluster_id)

    # print(settings.ISO_VM_FILE_FULL_PATH)

    # tfvars = {
    #     "vm_name": cluster.id,
    #     "cpu": cluster.cpu,
    #     "memory": cluster.ram_mb,
    #     "guest_os_type": "rocky-unknown",
    #     "disk_size": cluster.storage_gb * 1024,
    #     "iso_path": f"file:///{str(settings.ISO_VM_FILE_FULL_PATH)}",
    # }

    change_ip_address("192.168.100.10", "automation", "192.168.100.11")

    # with open(settings.TERRAFORM_DIR_FULL_PATH / "terraform.tfvars.json", "r") as f:
    #     vms: dict = json.loads(f.read())
    #     if vms.get("vms") is None:
    #         vms = {"vms": {}}

    #     vms["vms"][cluster.id[:6]] = {
    #         "cpu": cluster.cpu,
    #         "memory": cluster.ram_mb,
    #     }

    # with open(settings.TERRAFORM_DIR_FULL_PATH / "terraform.tfvars.json", "w") as f:
    #     json.dump(vms, f)

    # subprocess.run(
    #     ["terraform", "init"], cwd=str(settings.TERRAFORM_DIR_FULL_PATH), check=True
    # )

    # subprocess.run(
    #     ["terraform", "apply", "-auto-approve"],
    #     cwd=str(settings.TERRAFORM_DIR_FULL_PATH),
    #     check=True,
    # )


def change_ip_address(host: str, username: str, new_ip: str):
    """Меняет IP адрес на виртуальной машине на заданный"""
    password = "10021984qW"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=username, password=password)

    # Читаем текущий конфиг
    cmd = f"echo {password} | sudo -S cat /etc/netplan/01-netcfg.yaml"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdin.write(password + "\n")
    stdin.flush()
    content = stdout.read().decode()

    # Парсим YAML
    config = yaml.safe_load(content)

    # Получаем маску
    addr: str = config["network"]["ethernets"]["eth0"]["addresses"][0]
    if addr and "/" in addr:
        mask = addr.split("/")[-1]
    else:
        mask = "24"  # строка, а не число

    # Меняем IP
    config["network"]["ethernets"]["eth0"]["addresses"] = [f"{new_ip}/{mask}"]

    # Преобразуем в строку
    new_content = yaml.dump(config, sort_keys=False)

    # Записываем новое содержимое во временный файл
    temp_file_path = "/tmp/01-netcfg-tmp.yaml"
    cmd = f"cat > {temp_file_path}"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdin.write(new_content)
    stdin.channel.shutdown_write()
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Failed to write temp file: {stderr.read().decode()}")
        ssh.close()
        return

    # Копируем временный файл в целевой с правами sudo
    cmd = f"echo {password} | sudo -S cp {temp_file_path} /etc/netplan/01-netcfg.yaml"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdin.write(password + "\n")
    stdin.flush()
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Failed to copy file: {stderr.read().decode()}")
        ssh.close()
        return

    # Применяем netplan
    cmd = f"echo {password} | sudo -S netplan apply"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdin.write(password + "\n")
    stdin.flush()
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Failed to apply netplan: {stderr.read().decode()}")
        ssh.close()
        return

    print(f"IP address changed to {new_ip}/{mask}")
    ssh.close()
