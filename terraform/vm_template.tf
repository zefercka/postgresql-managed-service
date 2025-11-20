terraform {
  required_providers {
    hyperv = {
      source  = "registry.terraform.io/taliesins/hyperv"
      version = "1.2.1"
    }
  }
}

provider "hyperv" {
  host     = var.hyperv_hosts[values(var.vms)[length(values(var.vms)) - 1].host].host
  port     = var.hyperv_hosts[values(var.vms)[length(values(var.vms)) - 1].host].port
  https    = var.hyperv_hosts[values(var.vms)[length(values(var.vms)) - 1].host].https
  insecure = true
  user     = var.hyperv_hosts[values(var.vms)[length(values(var.vms)) - 1].host].user
  password = var.hyperv_hosts[values(var.vms)[length(values(var.vms)) - 1].host].password
  timeout  = "200s"
}

resource "time_sleep" "wait_after_create_disk" {
  create_duration = "20s"
  depends_on      = [hyperv_vhd.disk]
}

# --- Сетевой свитч ---
resource "hyperv_network_switch" "dmz" {
  depends_on = [time_sleep.wait_after_create_disk]

  name                = "DMZ"
  switch_type         = "Internal"
}

resource "null_resource" "set_internal_switch_ip" {
  for_each = var.vms

  depends_on = [hyperv_network_switch.dmz]

  connection {
    type     = "winrm"
    host     = var.hyperv_hosts[each.value.host].host
    port     = var.hyperv_hosts[each.value.host].port
    https    = var.hyperv_hosts[each.value.host].https
    user     = var.hyperv_hosts[each.value.host].user
    password = var.hyperv_hosts[each.value.host].password
    insecure = true
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -Command \"$ifAlias = 'vEthernet (DMZ)'; if (-not (Get-NetIPAddress -InterfaceAlias $ifAlias -ErrorAction SilentlyContinue)) { New-NetIPAddress -IPAddress 192.168.100.1 -PrefixLength 24 -InterfaceAlias $ifAlias }\"",
    ]
  }
}

resource "null_resource" "create_nat" {
  for_each = var.hyperv_hosts

  depends_on = [null_resource.set_internal_switch_ip] 

  connection {
    type     = "winrm"
    host     = each.value.host
    user     = each.value.user
    password = each.value.password
    https    = each.value.https
    insecure = true
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -Command \"if (-not (Get-NetNat -Name 'InternalNatNetwork' -ErrorAction SilentlyContinue)) { New-NetNat -Name 'InternalNatNetwork' -InternalIPInterfaceAddressPrefix '192.168.100.0/24' }\""
    ]
  }
}

# --- Диск VM ---
resource "hyperv_vhd" "disk" {
  for_each = var.vms

  path       = "D:\\VMS\\disks\\${each.key}.vhdx"
  size       = 10 * 1024 * 1024 * 1024     # 10GB
  source = each.value.source_disk_path
}

# --- Виртуальная машина ---
resource "hyperv_machine_instance" "vm" {
  for_each = var.vms

  name        = each.key
  generation  = 2
  processor_count = each.value.cpu
  memory_startup_bytes = each.value.memory * 1024 * 1024 # 2 GB
  static_memory = true
  state        = "Running"

  depends_on = [
    hyperv_vhd.disk,
    time_sleep.wait_after_create_disk,
    hyperv_network_switch.dmz,
    null_resource.create_nat,
  ]

  # Диск
  hard_disk_drives {
    controller_type   = "Scsi"
    controller_number = "0"
    controller_location = "0"
    path              = hyperv_vhd.disk[each.key].path
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
}

resource "null_resource" "port_forward_old_ip" {
  depends_on = [hyperv_machine_instance.vm]

  triggers = {
    vm_ids = join(",", values(hyperv_machine_instance.vm)[*].id)
  }

  provisioner "remote-exec" {
    connection {
      type     = "winrm"
      host     = var.hyperv_hosts[length(values(var.vms)) - 1].host
      user     = var.hyperv_hosts[length(values(var.vms)) - 1].user
      password = var.hyperv_hosts[length(values(var.vms)) - 1].password
      https    = var.hyperv_hosts[length(values(var.vms)) - 1].https
      insecure = true
    }

    inline = [
      # Проброс портов на старый IP
      "Set-NetNatStaticMapping -NatName 'VMNat' -Protocol TCP -ExternalIPAddress 0.0.0.0 -ExternalPort 22222 -InternalIPAddress ${var.base_ip} -InternalPort 22",
      "Set-NetNatStaticMapping -NatName 'VMNat' -Protocol TCP -ExternalIPAddress 0.0.0.0 -ExternalPort 15432 -InternalIPAddress ${var.base_ip} -InternalPort 5432"
    ]
  }
}

resource "null_resource" "find_free_ip_remote" {
  for_each = var.hyperv_hosts

  connection {
    type     = "winrm"
    host     = each.value.host
    user     = each.value.user
    password = each.value.password
    https    = each.value.https
    insecure = true
  }

  provisioner "remote-exec" {
    inline = [
      # PowerShell ищет свободный IP в сети 192.168.100.0/24
      "$candidate_ips = 20..254 | ForEach-Object { '192.168.100.' + $_ }",
      "foreach ($ip in $candidate_ips) {",
      "  if (-not (Test-Connection -ComputerName $ip -Count 1 -Quiet)) {",
      "    Set-Content -Path C:\\temp\\free_ip.txt -Value $ip",
      "    break",
      "  }",
      "}"
    ]
  }
}

# data "remote_file" "free_ip" {
#   depends_on = [null_resource.find_free_ip_remote]
#   host       = var.hyperv_hosts[length(values(var.vms)) - 1].host
#   user       = var.hyperv_hosts[length(values(var.vms)) - 1].user
#   password   = var.hyperv_hosts[length(values(var.vms)) - 1].password
#   https      = var.hyperv_hosts[length(values(var.vms)) - 1].https
#   insecure   = true
#   source     = "C:\\temp\\free_ip.txt"
# }

resource "null_resource" "set_vm_ip" {
  depends_on = [hyperv_machine_instance.vm]

  triggers = {
    # Запускать каждый раз при изменении VM
    vm_ids = join(",", values(hyperv_machine_instance.vm)[*].id)
  }

  connection {
    type     = "winrm"
    host     = var.hyperv_hosts[length(values(var.vms)) - 1].host
    user     = var.hyperv_hosts[length(values(var.vms)) - 1].user
    password = var.hyperv_hosts[length(values(var.vms)) - 1].password
    https    = var.hyperv_hosts[length(values(var.vms)) - 1].https
    insecure = true
  }

  provisioner "remote-exec" {
    inline = [
      "if (Test-Path C:\\temp\\free_ip.txt) { Get-Content C:\\temp\\free_ip.txt } else { exit 1 }"
    ]
  }

  provisioner "local-exec" {
    command = <<EOT
ansible-playbook ansible/vm/change_vm_ip.yaml \
  -e "new_ip=${replace(self.connection_std_out, "\r\n$", "")}" \
  -e "netmask=${var.netmask}" \
  -e "gateway=${var.gateway}" \
  -e "ansible_user=${var.base_user}" \
  -e "ansible_ssh_private_key_file=${var.ssh_key}" \
  -i "${var.base_ip},"
EOT
  }
}

resource "null_resource" "set_vm_ip" {
  depends_on = [null_resource.port_forward_old_ip]

  triggers = {
    vm_ids = join(",", values(hyperv_machine_instance.vm)[*].id)
  }

  connection {
    type     = "winrm"
    host     = var.hyperv_hosts[length(values(var.vms)) - 1].host
    user     = var.hyperv_hosts[length(values(var.vms)) - 1].user
    password = var.hyperv_hosts[length(values(var.vms)) - 1].password
    https    = var.hyperv_hosts[length(values(var.vms)) - 1].https
    insecure = true
  }

  provisioner "remote-exec" {
    inline = [
      # Получение нового IP
      "if (Test-Path C:\\temp\\free_ip.txt) { Get-Content C:\\temp\\free_ip.txt } else { exit 1 }"
    ]
  }

provisioner "local-exec" {
    command = <<EOT
ansible-playbook ansible/vm/change_vm_ip.yaml \
  -e "new_ip=${replace(self.connection_std_out, "\r\n$", "")}" \
  -e "netmask=${var.netmask}" \
  -e "gateway=${var.gateway}" \
  -e "ansible_user=${var.base_user}" \
  -e "ansible_ssh_private_key_file=${var.ssh_key}" \
  -i "${var.hyperv_hosts[length(values(var.vms)) - 1].host}, -p ${var.proxied_ssh_port}"
EOT
  }
}

# resource "null_resource" "set_vm_ip" {
#   depends_on = [hyperv_machine_instance.vm, data.remote_file.free_ip]

#   provisioner "local-exec" {
#     command = <<EOT
# ansible-playbook ansible/vm/change_vm_ip.yaml \
#   -e "new_ip=${trim(data.remote_file.free_ip.content)}" \
#   -e "netmask=${var.netmask}" \
#   -e "gateway=${var.gateway}" \
#   -e "ansible_user=${var.base_user}" \
#   -e "ansible_ssh_private_key_file=${var.ssh_key}" \
#   -i "${var.base_ip},"
# EOT
#   }
# }

resource "null_resource" "output" {
  for_each = var.vms

  depends_on = [
    null_resource.set_vm_ip
  ]

  triggers = {
    vm_name = each.key
  }

  connection {
    type     = "winrm"
    host     = var.hyperv_hosts[each.value.host].host
    port     = var.hyperv_hosts[each.value.host].port
    https    = var.hyperv_hosts[each.value.host].https
    user     = var.hyperv_hosts[each.value.host].user
    password = var.hyperv_hosts[each.value.host].password
    insecure = true
  }

  provisioner "remote-exec" {
    inline = [
      "(Get-VM -Name '${self.triggers.vm_name}' | Get-VMNetworkAdapter).IPAddresses[0]"
    ]
  }
}

wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
apt update && apt install terraform