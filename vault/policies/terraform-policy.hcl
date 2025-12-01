# Политика доступа для Terraform сервиса
# Предоставляет минимально необходимые права (Principle of Least Privilege)

# Доступ к секретам Hyper-V
path "secret/data/hyperv/*" {
  capabilities = ["read", "list"]
}

# Доступ к секретам PostgreSQL
path "secret/data/postgresql/*" {
  capabilities = ["read", "list"]
}

# Доступ к SSH ключам
path "secret/data/ssh/*" {
  capabilities = ["read", "list"]
}

# Доступ к секретам конфигурации
path "secret/data/config/*" {
  capabilities = ["read", "list"]
}

# Доступ к метаданным секретов
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
