variable "hyperv_hosts" {
  description = "Параметры хостов для создания ВМ"
  type = map(object({
    host     = string
    port     = number
    user     = string
    password = string
    https    = bool
  }))
}

variable "vms" {
  description = "Описание виртуальных машин"
  type = map(object({
    cpu              = number
    memory           = number
    source_disk_path = string
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
  default = "../keys/servers/ssh_key"
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