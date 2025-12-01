FROM hashicorp/vault:1.21

USER root
RUN apk add --no-cache openssl

WORKDIR /vault

RUN mkdir -p /vault/config \
             /vault/data \
             /vault/certs \
             /vault/policies \
             /vault/scripts \
             /vault/init \
             /vault/logs && \
    chown -R vault:vault /vault && \
    chmod 755 /vault/data /vault/certs /vault/init /vault/logs

COPY vault/config-dev.hcl /vault/config/config-dev.hcl
COPY vault/policies/*.hcl /vault/policies/

RUN chown -R vault:vault /vault && \
    chmod 755 /vault/scripts && \
    chmod 755 /vault/init && \
    chmod 755 /vault/logs && \
    chmod 755 /vault/data

# Используем CMD с упрощенным скриптом (используем jq для парсинга JSON)
RUN apk add --no-cache jq

CMD sh -c 'vault server -config=/vault/config/config-dev.hcl & VAULT_PID=$!; sleep 15; export VAULT_ADDR=http://127.0.0.1:8200; if vault operator init -status 2>&1 | grep -q "not initialized"; then vault operator init -key-shares=5 -key-threshold=3 -format=json > /vault/init/vault-init.json; chmod 600 /vault/init/vault-init.json; KEY1=$(jq -r ".unseal_keys_b64[0]" /vault/init/vault-init.json); KEY2=$(jq -r ".unseal_keys_b64[1]" /vault/init/vault-init.json); KEY3=$(jq -r ".unseal_keys_b64[2]" /vault/init/vault-init.json); vault operator unseal "$KEY1"; vault operator unseal "$KEY2"; vault operator unseal "$KEY3"; ROOT_TOKEN=$(jq -r ".root_token" /vault/init/vault-init.json); export VAULT_TOKEN="$ROOT_TOKEN"; echo "$ROOT_TOKEN" > /vault/token; chmod 640 /vault/token; vault secrets enable -version=2 -path=secret kv || true; vault policy write terraform /vault/policies/terraform-policy.hcl || true; vault auth enable approle || true; vault audit enable file file_path=/vault/logs/audit.log || true; fi; if vault status | grep -q "Sealed.*true"; then KEY1=$(jq -r ".unseal_keys_b64[0]" /vault/init/vault-init.json); KEY2=$(jq -r ".unseal_keys_b64[1]" /vault/init/vault-init.json); KEY3=$(jq -r ".unseal_keys_b64[2]" /vault/init/vault-init.json); vault operator unseal "$KEY1"; vault operator unseal "$KEY2"; vault operator unseal "$KEY3"; fi; echo "Vault готов!"; echo "UI: http://localhost:8200/ui"; echo "СОХРАНИТЕ файл /vault/init/vault-init.json!"; wait $VAULT_PID'