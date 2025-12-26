#!/bin/sh
set -e

# Запускаем Vault сервер в фоне
vault server -config=/vault/config/config-dev.hcl &
VAULT_PID=$!

# Ждем запуска Vault
sleep 15

export VAULT_ADDR=http://127.0.0.1:8200

# Проверяем, инициализирован ли Vault
if vault operator init -status 2>&1 | grep -q "not initialized"; then
    echo "Инициализация Vault..."
    
    # Инициализируем Vault
    vault operator init -key-shares=5 -key-threshold=3 -format=json > /vault/init/vault-init.json
    chmod 600 /vault/init/vault-init.json
    
    # Извлекаем ключи для unseal
    KEY1=$(jq -r ".unseal_keys_b64[0]" /vault/init/vault-init.json)
    KEY2=$(jq -r ".unseal_keys_b64[1]" /vault/init/vault-init.json)
    KEY3=$(jq -r ".unseal_keys_b64[2]" /vault/init/vault-init.json)
    
    # Unsealing Vault
    vault operator unseal "$KEY1"
    vault operator unseal "$KEY2"
    vault operator unseal "$KEY3"
    
    # Получаем root token
    ROOT_TOKEN=$(jq -r ".root_token" /vault/init/vault-init.json)
    export VAULT_TOKEN="$ROOT_TOKEN"
    
    # Сохраняем token
    mkdir -p /vault/token-storage
    echo "$ROOT_TOKEN" > /vault/token-storage/root-token
    chmod 644 /vault/token-storage/root-token
    chown vault:vault /vault/token-storage/root-token
    
    # Настройка Vault
    echo "Создание структуры секретов..."
    
    # Включаем KV v2 engines для разных типов секретов
    vault secrets enable -version=2 -path=secret kv || true
    vault secrets enable -version=2 -path=hyperv_hosts kv || true
    vault secrets enable -version=2 -path=clusters kv || true
    vault secrets enable -version=2 -path=ssh_keys kv || true
    
    echo "✓ KV engines созданы"
    
    # Создаем политики доступа
    vault policy write terraform /vault/policies/terraform-policy.hcl || true
    vault policy write server /vault/policies/server-policy.hcl || true
    vault policy write admin /vault/policies/admin-policy.hcl || true
    vault policy write readonly /vault/policies/readonly-policy.hcl || true
    
    echo "✓ Политики доступа созданы"
    
    # Включаем методы аутентификации
    vault auth enable approle || true
    
    echo "✓ AppRole аутентификация включена"
    
    # Включаем аудит
    vault audit enable file file_path=/vault/logs/audit.log || true
    
    echo "✓ Аудит включен"
    
    # Настройка AppRole для Terraform
    vault write auth/approle/role/terraform \
        token_policies="terraform" \
        token_ttl=1h \
        token_max_ttl=4h \
        secret_id_ttl=0 \
        secret_id_num_uses=0
    
    echo "✓ AppRole для Terraform настроен"
    
    # Получаем и сохраняем AppRole credentials для Terraform
    ROLE_ID=$(vault read -field=role_id auth/approle/role/terraform/role-id)
    SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/terraform/secret-id)
    
    echo "$ROLE_ID" > /vault/approle/terraform-role-id
    echo "$SECRET_ID" > /vault/approle/terraform-secret-id
    chmod 600 /vault/approle/terraform-role-id /vault/approle/terraform-secret-id
    chown vault:vault /vault/approle/terraform-role-id /vault/approle/terraform-secret-id
    
    echo "AppRole настроен для Terraform:"
    echo "  Role ID: $ROLE_ID"
    echo "  Secret ID сохранен в /vault/approle/terraform-secret-id"
    
    # Настройка AppRole для Server
    vault write auth/approle/role/server \
        token_policies="server" \
        token_ttl=1h \
        token_max_ttl=8h \
        secret_id_ttl=0 \
        secret_id_num_uses=0
    
    echo "✓ AppRole для Server настроен"
    
    # Получаем и сохраняем AppRole credentials для Server
    SERVER_ROLE_ID=$(vault read -field=role_id auth/approle/role/server/role-id)
    SERVER_SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/server/secret-id)
    
    echo "$SERVER_ROLE_ID" > /vault/approle/server-role-id
    echo "$SERVER_SECRET_ID" > /vault/approle/server-secret-id
    chmod 600 /vault/approle/server-role-id /vault/approle/server-secret-id
    chown vault:vault /vault/approle/server-role-id /vault/approle/server-secret-id
    
    echo "AppRole настроен для Server:"
    echo "  Role ID: $SERVER_ROLE_ID"
    echo "  Secret ID сохранен в /vault/approle/server-secret-id"
    
    echo "Vault инициализирован!"
fi

# Проверяем, не запечатан ли Vault
if vault status | grep -q "Sealed.*true"; then
    echo "Vault запечатан, выполняем unseal..."
    
    KEY1=$(jq -r ".unseal_keys_b64[0]" /vault/init/vault-init.json)
    KEY2=$(jq -r ".unseal_keys_b64[1]" /vault/init/vault-init.json)
    KEY3=$(jq -r ".unseal_keys_b64[2]" /vault/init/vault-init.json)
    
    vault operator unseal "$KEY1"
    vault operator unseal "$KEY2"
    vault operator unseal "$KEY3"
fi

echo "=========================================="
echo "Vault готов!"
echo "UI: http://localhost:8200/ui"
echo "СОХРАНИТЕ файл /vault/init/vault-init.json"
echo "=========================================="

# Ждем процесс Vault
wait $VAULT_PID
