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
  token = var.vault_token_file != "" ? chomp(file(var.vault_token_file)) : null
}

# Инициализация Vault хранилища для хостов
data "vault_kv_secret_v2" "host" {
  mount = "hyperv_hosts"
  name  = var.hyperv_host.id
}

locals {
  hyperv_host_user = data.vault_kv_secret_v2.host.data["user"]
  hyperv_host_pass = data.vault_kv_secret_v2.host.data["password"]
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

# Ресурс для ожидания после создания диска, потому что может упасть ошибка
# что файл ещё занят
resource "time_sleep" "wait_after_create_disk" {
  create_duration = "20s"
  depends_on      = [hyperv_vhd.disk]
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

  provisioner "remote-exec" {
    inline = [
      "powershell -Command \"Start-Sleep -Seconds 5; $ifAlias = 'vEthernet (DMZ)'; if (-not (Get-NetIPAddress -InterfaceAlias $ifAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -eq '192.168.100.1' })) { Remove-NetIPAddress -InterfaceAlias $ifAlias -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue; New-NetIPAddress -IPAddress 192.168.100.1 -PrefixLength 24 -InterfaceAlias $ifAlias }\"",
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

  provisioner "remote-exec" {
    inline = [
      "powershell -Command \"if (-not (Get-NetNat -Name 'InternalNatNetwork' -ErrorAction SilentlyContinue)) { New-NetNat -Name 'InternalNatNetwork' -InternalIPInterfaceAddressPrefix '192.168.100.0/24' }\""
    ]
  }
}

# Диск для ВМ (копируется из уже существующего)
resource "hyperv_vhd" "disk" {
  for_each = var.vms

  path     = "${disks_path}\\${each.key}.vhdx"
  size     = each.value.disk_size * 1024 * 1024 * 1024
  source   = each.value.source_disk_path
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

  provisioner "remote-exec" {
    connection {
      type     = "winrm"
      host     = var.hyperv_host.host
      user     = local.hyperv_host_user
      password = local.hyperv_host_pass
      https    = var.hyperv_host.https
      insecure = true
    }

    inline = [
      "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"$natName = 'InternalNatNetwork'; $internalIP = '${var.base_ip}'; $port = 22; $exists = Get-NetNatStaticMapping -NatName $natName -ErrorAction SilentlyContinue | Where-Object { $_.ExternalPort -eq $port -and $_.Protocol -eq 'TCP' }; if ($exists) { Write-Host 'Port forwarding already exists. Skipping.' } else { Write-Host 'Creating NAT port forward for port', $port, '...'; Add-NetNatStaticMapping -NatName $natName -Protocol TCP -ExternalIPAddress '0.0.0.0' -ExternalPort $port -InternalIPAddress $internalIP -InternalPort $port; Write-Host 'Port forward created.' }\""
    ]
  }
}

# Поиск свободных IP в NAT сети
resource "null_resource" "find_free_ip_remote" {
  connection {
    type     = "winrm"
    host     = var.hyperv_host.host
    user     = local.hyperv_host_user
    password = local.hyperv_host_pass
    https    = var.hyperv_host.https
    insecure = true
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -Command \"if (!(Test-Path -Path 'C:\\Temp' -PathType Container)) { New-Item -ItemType Directory -Path 'C:\\Temp' -Force }\"",
      "powershell -Command \"$candidate_ips = 20..254 | ForEach-Object { '192.168.100.' + $_ }; foreach ($ip in $candidate_ips) { if (-not (Test-Connection -ComputerName $ip -Count 1 -Quiet)) { Set-Content -Path 'C:\\Temp\\free_ip.txt' -Value $ip; break } }\""
    ]
  }

  provisioner "local-exec" {
    command = "scp -o StrictHostKeyChecking=no ${local.hyperv_host_user}@${var.hyperv_host.host}:C:/Temp/free_ip.txt ./local_free_ip.txt"
  }
}

data "local_file" "free_ip" {
  depends_on = [ null_resource.find_free_ip_remote ]

  filename = "./local_free_ip.txt"
}

# Установка найденного IP в виртуалку (тут возможно надо доработать как-то, сейчас получается
# что IP только для последней виртуалки, но в целом так и должо быть)
resource "null_resource" "set_vm_ip" {
  depends_on = [hyperv_machine_instance.vm, data.local_file.free_ip, null_resource.hyperv_nat_port22]

  provisioner "local-exec" {
    environment = {
      ANSIBLE_HOST_KEY_CHECKING = "False"
    }
    command = "ansible-playbook ../../ansible/vm/change_vm_ip.yaml -e new_ip=${trimspace(data.local_file.free_ip.content)} -e netmask=${var.netmask} -e gateway=${var.gateway} -e ansible_user=automation -i ${var.hyperv_host.host}, -e ansible_port=${var.proxied_ssh_port} --private-key=${var.ssh_key}"
  }
}

# Прокидывает свободные порты для SSH и PostgreSQL на новом IP
resource "null_resource" "port_forward_new_ip" {
  depends_on = [null_resource.set_vm_ip]

  provisioner "remote-exec" {
    connection {
      type     = "winrm"
      host     = var.hyperv_host.host
      user     = local.hyperv_host_user
      password = local.hyperv_host_pass
      https    = var.hyperv_host.https
      insecure = true
    }

    inline = [
       "powershell -Command \"& { $natName = 'InternalNatNetwork'; $startPort = 20000; $sshInternalIP = '${trimspace(data.local_file.free_ip.content)}'; $pgInternalIP = '${trimspace(data.local_file.free_ip.content)}'; function Find-FreePort { param([int]$Start); for ($p = $Start; $p -le 65535; $p++) { if (-not (Test-NetConnection -ComputerName 127.0.0.1 -Port $p -WarningAction SilentlyContinue).TcpTestSucceeded) { if (-not (Get-NetNatStaticMapping -NatName $natName -ErrorAction SilentlyContinue | Where-Object { $_.ExternalPort -eq $p })) { return $p } } } throw 'Нет свободных портов.' }; $sshPort = Find-FreePort -Start $startPort; $pgPort = Find-FreePort -Start ($sshPort + 1); Write-Host \\\"Найден свободный порт для SSH: $sshPort\\\"; Write-Host \\\"Найден свободный порт для PostgreSQL: $pgPort\\\"; Add-NetNatStaticMapping -NatName $natName -Protocol TCP -ExternalIPAddress 0.0.0.0 -ExternalPort $sshPort -InternalIPAddress $sshInternalIP -InternalPort 22; Add-NetNatStaticMapping -NatName $natName -Protocol TCP -ExternalIPAddress 0.0.0.0 -ExternalPort $pgPort -InternalIPAddress $pgInternalIP -InternalPort 5432; Set-Content -Path 'C:\\Temp\\nat_ports.txt' -Value \\\"SSH=$sshPort;PG=$pgPort\\\" }\""
    ]
  }

  provisioner "local-exec" {
    command = "scp -o StrictHostKeyChecking=no ${local.hyperv_host_user}@${var.hyperv_host.host}:C:/Temp/nat_ports.txt ./local_free_ports.txt"
  }
}

data "local_file" "free_ports" {
  depends_on = [ null_resource.port_forward_new_ip ]
  filename = "./local_free_ports.txt"
}

locals {
  raw_content = chomp(data.local_file.free_ports.content)
  pairs       = split(";", local.raw_content)
  port_map    = {
    for pair in local.pairs : 
    split("=", pair)[0] => tonumber(split("=", pair)[1])
  }
}

output "vm_ip" {
  description = "Новый IP виртуальной машины"
  value       = trimspace(data.local_file.free_ip.content)
}

output "ssh_port" {
  description = "Внешний SSH порт, проброшенный NAT"
  value       = local.port_map["SSH"]
}

output "postgres_port" {
  description = "Внешний PostgreSQL порт, проброшенный NAT"
  value       = local.port_map["PG"]
}