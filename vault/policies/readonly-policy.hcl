# Политика только для чтения
# Для сервисов, которым нужен только доступ на чтение

# Чтение всех секретов
path "secret/data/*" {
  capabilities = ["read", "list"]
}

# Просмотр метаданных
path "secret/metadata/*" {
  capabilities = ["list", "read"]
}

# Обновление своего токена
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Проверка своего токена
path "auth/token/lookup-self" {
  capabilities = ["read"]
}
