terraform {
  required_providers {
    vault = {
      source = "hashicorp/vault"
      version = "3.23.0"
    }
    hyperv = {
      source  = "registry.terraform.io/taliesins/hyperv"
      version = "1.2.1"
    }
  }
}

provider "vault" {
  # Используем AppRole для аутентификации вместо токена
  auth_login {
    path = "auth/approle/login"

    parameters = {
      role_id   = chomp(file(var.vault_role_id_file))
      secret_id = chomp(file(var.vault_secret_id_file))
    }
  }
}

# Инициализация Vault хранилища для хостов
data "vault_kv_secret_v2" "host" {
  mount = "hyperv_hosts"
  name  = var.hyperv_host.id
}

data "vault_kv_secret_v2" "cluster" {
  for_each = var.vms

  mount = "clusters"
  name  = "${each.key}/users/super"
}

locals {
  hyperv_host_user = data.vault_kv_secret_v2.host.data["username"]
  hyperv_host_pass = data.vault_kv_secret_v2.host.data["password"]

  postgres_super_user = {
    for cluster, _ in var.vms :
    cluster => data.vault_kv_secret_v2.cluster[cluster].data["username"]
  }

  postgres_super_pass = {
    for cluster, _ in var.vms :
    cluster => data.vault_kv_secret_v2.cluster[cluster].data["password"]
  }
}

# Инициализация провайдера для создания ВМ
provider "hyperv" {
  host     = var.hyperv_host.host
  port     = var.hyperv_host.port
  https    = var.hyperv_host.https
  insecure = true
  user     = local.hyperv_host_user
  password = local.hyperv_host_pass
  timeout  = "200s"
}

# Сетевой свитч
resource "hyperv_network_switch" "dmz" {
  depends_on = [time_sleep.wait_after_create_disk]

  name                = "DMZ"
  switch_type         = "Internal"
}

# Установка IP для нового свитча
resource "null_resource" "set_internal_switch_ip" {
  depends_on = [hyperv_network_switch.dmz]

  connection {
    type     = "winrm"
    host     = var.hyperv_host.host
    port     = var.hyperv_host.port
    https    = var.hyperv_host.https
    user     = local.hyperv_host_user
    password = local.hyperv_host_pass
    insecure = true
  }

  provisioner "file" {
    source      = "../scripts/set_switch_ip.ps1"
    destination = "C:/Temp/set_switch_ip.ps1"
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -ExecutionPolicy Bypass -File C:/Temp/set_switch_ip.ps1",
    ]
  }
}

# Создание NAT сети 192.168.100.0/24
resource "null_resource" "create_nat" {
  depends_on = [null_resource.set_internal_switch_ip] 

  connection {
    type     = "winrm"
    host     = var.hyperv_host.host
    user     = local.hyperv_host_user
    password = local.hyperv_host_pass
    https    = var.hyperv_host.https
    insecure = true
  }

  provisioner "file" {
    source      = "../scripts/create_nat.ps1"
    destination = "C:/Temp/create_nat.ps1"
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -ExecutionPolicy Bypass -File C:/Temp/create_nat.ps1 -NatName 'InternalNatNetwork' -InternalIPInterfaceAddressPrefix '192.168.100.0/24'"
    ]
  }
}

# Диск для ВМ (копируется из уже существующего)
resource "hyperv_vhd" "disk" {
  for_each = var.vms

  path     = "${var.hyperv_host.disks_path}\\${each.key}.vhdx"
  size     = each.value.disk_size * 1024 * 1024 * 1024
  source   = each.value.source_disk_path
}

# Ресурс для ожидания после создания диска, потому что может упасть ошибка
# что файл ещё занят
resource "time_sleep" "wait_after_create_disk" {
  create_duration = "20s"
  depends_on      = [hyperv_vhd.disk]
}

# Виртуальная машина
resource "hyperv_machine_instance" "vm" {
  for_each = var.vms

  name                 = each.key
  generation           = 2
  processor_count      = each.value.cpu
  memory_startup_bytes = each.value.memory * 1024 * 1024
  static_memory        = true
  state                = "Running"

  depends_on = [
    hyperv_vhd.disk,
    time_sleep.wait_after_create_disk,
    hyperv_network_switch.dmz,
    null_resource.create_nat,
  ]

  lifecycle {
    ignore_changes = [
      vm_firmware[0].boot_order
    ]
  }

  # Диск
  hard_disk_drives {
    controller_type     = "Scsi"
    controller_number   = "0"
    controller_location = "0"
    path                = hyperv_vhd.disk[each.key].path
  }

  # Сеть
  network_adaptors {
    switch_name = hyperv_network_switch.dmz.name
    name = "nat"
  }

  vm_firmware {
    enable_secure_boot = "Off"

    boot_order {
      boot_type           = "HardDiskDrive"
      controller_number   = "0"
      controller_location = "0"
    }
  }

  # Настройки процессора, установлены по умолчанию, потому что при повторном запуске
  # оно ставится в null почему-то 
  vm_processor {
    compatibility_for_migration_enabled               = false
    compatibility_for_older_operating_systems_enabled = false
    enable_host_resource_protection                   = false
    expose_virtualization_extensions                  = false
    hw_thread_count_per_core                          = 0
    maximum                                           = 100
    maximum_count_per_numa_node                       = 16
    maximum_count_per_numa_socket                     = 1
    relative_weight                                   = 100
    reserve                                           = 0
  }
}

# Прокидывает 22 порт (ssh) из дефолтной виртуалки (по умолчанию - 192.168.100.10) на 22222
resource "null_resource" "hyperv_nat_port22" {
  depends_on = [ hyperv_machine_instance.vm ]

  connection {
    type     = "winrm"
    host     = var.hyperv_host.host
    user     = local.hyperv_host_user
    password = local.hyperv_host_pass
    https    = var.hyperv_host.https
    insecure = true
  }

  provisioner "file" {
    source      = "../scripts/add_initial_port_mapping.ps1"
    destination = "C:/Temp/add_initial_port_mapping.ps1"
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -ExecutionPolicy Bypass -File C:/Temp/add_initial_port_mapping.ps1 -InternalIP ${var.base_ip}"
    ]
  }
}

# Поиск свободных IP в NAT сети с механизмом блокировки (для каждой ВМ отдельно)
resource "null_resource" "find_free_ip_remote" {
  for_each = var.vms

  connection {
    type     = "winrm"
    host     = var.hyperv_host.host
    user     = local.hyperv_host_user
    password = local.hyperv_host_pass
    https    = var.hyperv_host.https
    insecure = true
  }

  provisioner "file" {
    source      = "../scripts/find_free_ip.ps1"
    destination = "C:/Temp/find_free_ip_${each.key}.ps1"
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -ExecutionPolicy Bypass -File C:/Temp/find_free_ip_${each.key}.ps1 -OutputFile C:/Temp/free_ip_${each.key}.txt"
    ]
  }

  provisioner "local-exec" {
    command = "sshpass -p '${local.hyperv_host_pass}' scp -o StrictHostKeyChecking=no ${local.hyperv_host_user}@${var.hyperv_host.host}:C:/Temp/free_ip_${each.key}.txt ./local_free_ip_${each.key}.txt"
  }
}

data "local_file" "free_ip" {
  for_each = var.vms
  depends_on = [null_resource.find_free_ip_remote]

  filename = "./local_free_ip_${each.key}.txt"
}

# Установка найденного IP в виртуалку
resource "null_resource" "set_vm_ip" {
  depends_on = [hyperv_machine_instance.vm, data.local_file.free_ip, null_resource.hyperv_nat_port22]

  for_each = var.vms

  provisioner "local-exec" {
    environment = {
      ANSIBLE_HOST_KEY_CHECKING = "False"
    }
    command = "ansible-playbook ../../ansible/change_vm_ip.yaml -e new_ip=${trimspace(data.local_file.free_ip[each.key].content)} -e netmask=${var.netmask} -e gateway=${var.gateway} -e ansible_user=automation -i ${var.hyperv_host.host}, -e ansible_port=${var.proxied_ssh_port} --private-key=${var.ssh_key}"
  }

  # Освобождаем блокировку IP после успешного назначения
  connection {
    type     = "winrm"
    host     = var.hyperv_host.host
    user     = local.hyperv_host_user
    password = local.hyperv_host_pass
    https    = var.hyperv_host.https
    insecure = true
  }

  provisioner "file" {
    source      = "../scripts/unlock_ip.ps1"
    destination = "C:/Temp/unlock_ip_${each.key}.ps1"
  }


  provisioner "remote-exec" {
    when = create
    inline = [
      "powershell -ExecutionPolicy Bypass -File C:/Temp/unlock_ip_${each.key}.ps1 -IPAddress ${trimspace(data.local_file.free_ip[each.key].content)}"
    ]
  }
}

# Прокидывает свободные порты для SSH и PostgreSQL на новом IP
resource "null_resource" "port_forward_new_ip" {
  depends_on = [null_resource.set_vm_ip]

  for_each = var.vms

  connection {
    type     = "winrm"
    host     = var.hyperv_host.host
    user     = local.hyperv_host_user
    password = local.hyperv_host_pass
    https    = var.hyperv_host.https
    insecure = true
  }

  provisioner "file" {
    source      = "../scripts/add_nat_port_mapping.ps1"
    destination = "C:/Temp/add_nat_port_mapping_${each.key}.ps1"
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -ExecutionPolicy Bypass -File C:/Temp/add_nat_port_mapping_${each.key}.ps1 -InternalIP ${trimspace(data.local_file.free_ip[each.key].content)} -OutputFile C:/Temp/nat_ports_${each.key}.txt"
    ]
  }

  provisioner "local-exec" {
    command = "sshpass -p '${local.hyperv_host_pass}' scp -o StrictHostKeyChecking=no ${local.hyperv_host_user}@${var.hyperv_host.host}:C:/Temp/nat_ports_${each.key}.txt ./local_free_ports_${each.key}.txt"
  }
}

data "local_file" "free_ports" {
  for_each = var.vms
  depends_on = [null_resource.port_forward_new_ip]
  filename   = "./local_free_ports_${each.key}.txt"
}

locals {
  vm_configs = {
    for vm_name, vm in var.vms : vm_name => {
      raw_content = chomp(data.local_file.free_ports[vm_name].content)
      pairs       = split(";", chomp(data.local_file.free_ports[vm_name].content))
      port_map    = {
        for pair in split(";", chomp(data.local_file.free_ports[vm_name].content)) : 
        split("=", pair)[0] => tonumber(split("=", pair)[1])
      }
    }
  }
}

# Устанавливает PostgreSQL
resource "null_resource" "install_postgres" {
  depends_on = [data.local_file.free_ports]

  for_each = var.vms

  provisioner "local-exec" {
    environment = {
      ANSIBLE_HOST_KEY_CHECKING = "False"
    }

    command = "ansible-playbook ../../ansible/install_postgresql.yaml -e postgresql_version=${each.value.pg_version} -e ansible_user=automation -e db_name='${each.value.db_name}' -e db_user='${local.postgres_super_user[each.key]}' -e db_pass='${local.postgres_super_pass[each.key]}' -i ${var.hyperv_host.host}, -e ansible_port=${local.vm_configs[each.key].port_map["SSH"]} --private-key=${var.ssh_key}"
  }
}

output "vm_configs" {
  description = "Конфигурация всех созданных виртуальных машин"
  value = {
    for vm_name in keys(var.vms) : vm_name => {
      ip           = trimspace(data.local_file.free_ip[vm_name].content)
      ssh_port     = local.vm_configs[vm_name].port_map["SSH"]
      postgres_port = local.vm_configs[vm_name].port_map["PG"]
    }
  }
}

output "vm_ip" {
  description = "Новые IP виртуальных машин"
  value       = {
    for vm_name in keys(var.vms) : vm_name => trimspace(data.local_file.free_ip[vm_name].content)
  }
}

output "ssh_port" {
  description = "Внешние SSH порты, проброшенные NAT"
  value       = {
    for vm_name in keys(var.vms) : vm_name => local.vm_configs[vm_name].port_map["SSH"]
  }
}

output "postgres_port" {
  description = "Внешние PostgreSQL порты, проброшенные NAT"
  value       = {
    for vm_name in keys(var.vms) : vm_name => local.vm_configs[vm_name].port_map["PG"]
  }
}