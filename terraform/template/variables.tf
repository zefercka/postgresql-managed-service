variable "hyperv_host" {
  description = "Параметры хостов для создания ВМ"
  type = object({
    id    = number
    host  = string
    port  = number
    https = bool
    disks_path = {
      type = string
      description = "Путь к папке для хранения дисков виртуалок"
    }
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
  }))
  default = {}
}

variable "network_prefix" {
  type    = string
  default = "192.168.100"
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
  default = "/terraform/.ssh/id_rsa"
}

variable "base_ip" {
  type    = string
  default = "192.168.100.10"
}

variable "base_user" {
  type    = string
  default = "automation"
}

variable "proxied_ssh_port" {
  type    = string
  default = "22222"
}

variable "vault_token_file" {
  type = string
  default = "/vault/token"
}