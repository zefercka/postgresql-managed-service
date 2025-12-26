# Политика доступа для Terraform сервиса
# Предоставляет минимально необходимые права (Principle of Least Privilege)

# Доступ к секретам Hyper-V хостов
path "hyperv_hosts/data/*" {
  capabilities = ["read", "list"]
}

path "hyperv_hosts/metadata/*" {
  capabilities = ["list", "read"]
}

# Доступ к секретам PostgreSQL кластеров (только чтение для Terraform)
path "clusters/data/*" {
  capabilities = ["create", "read", "update", "list"]
}

path "clusters/metadata/*" {
  capabilities = ["create", "list", "read", "update"]
}

# Возможность создания дочернего токена (требуется для Terraform provider)
path "auth/token/create" {
  capabilities = ["create", "update"]
}

# Возможность обновления своего токена
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Возможность проверки своего токена
path "auth/token/lookup-self" {
  capabilities = ["read"]
}
