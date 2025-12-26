# Политика доступа для Server сервиса (FastAPI application)
# Предоставляет права на чтение и запись секретов кластеров

# Полный доступ к секретам PostgreSQL кластеров
path "clusters/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "clusters/metadata/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Доступ к секретам Hyper-V хостов (только чтение)
path "hyperv_hosts/data/*" {
  capabilities = ["read", "list"]
}

path "hyperv_hosts/metadata/*" {
  capabilities = ["list", "read"]
}

# Доступ к SSH ключам (только чтение)
path "ssh_keys/data/*" {
  capabilities = ["read", "list"]
}

# Доступ к метаданным
path "secret/metadata/*" {
  capabilities = ["list"]
}

# Возможность обновления своего токена
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Возможность проверки своего токена
path "auth/token/lookup-self" {
  capabilities = ["read"]
}
