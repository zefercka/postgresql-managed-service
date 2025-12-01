# Административная политика
# Полный доступ для администраторов системы

# Полный доступ к secrets
path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Управление политиками
path "sys/policies/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Управление auth методами
path "sys/auth/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Управление audit устройствами
path "sys/audit/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Управление mount points
path "sys/mounts/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Доступ к health статусу
path "sys/health" {
  capabilities = ["read"]
}

# Управление токенами
path "auth/token/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Управление AppRole
path "auth/approle/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
