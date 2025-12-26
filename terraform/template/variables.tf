variable "hyperv_host" {
  description = "Параметры хостов для создания ВМ"
  type = object({
    id         = number
    host       = string
    port       = number
    https      = bool
    disks_path = string  # Путь к папке для хранения дисков виртуалок
  })
}

variable "vms" {
  description = "Описание виртуальных машин"
  type = map(object({
    cpu              = number
    memory           = number
    source_disk_path = string
    disk_size        = number
    host             = string
    pg_version       = string
    db_name          = string
  }))
  default = {}
}

variable "gateway" {
  type    = string
  default = "192.168.100.1"
}

variable "netmask" {
  type    = number
  default = 24
}

variable "ssh_key" {
  type    = string
  default = "/home/terraform/.ssh/id_rsa"
}

variable "base_ip" {
  type    = string
  default = "192.168.100.10"
}

variable "base_user" {
  type    = string
  default = "automation"
}

# На этот порт по умолчанию проксится 22 порт с IP 192.168.100.10
# он же используется в скрипте add_initial_port_mapping.ps1
# если меняете здесь, то меняйте и там
variable "proxied_ssh_port" {
  type    = string
  default = "22222"
}

variable "vault_role_id_file" {
  type = string
  default = "/vault/approle/terraform-role-id"
  description = "Path to Vault AppRole role_id file"
}

variable "vault_secret_id_file" {
  type = string
  default = "/vault/approle/terraform-secret-id"
  description = "Path to Vault AppRole secret_id file"
}

variable "vault_approle_path" {
  type = string
  default = "auth/approle/login"
  description = "Path to Vault AppRole login endpoint"
}