FROM python:3.13-slim AS base

RUN apt-get update && \
    apt-get install -y openssh-server && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/postgresql-managed-service


FROM base AS python-deps-install

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

FROM python-deps-install AS migrations

COPY ./alembic.ini ./alembic.ini
COPY ./app/__init__.py /opt/postgresql-managed-service/app/__init__.py
COPY ./app/config.py /opt/postgresql-managed-service/app/config.py
COPY ./app/src /opt/postgresql-managed-service/app/src
COPY ./migrations /opt/postgresql-managed-service/migrations

CMD ["alembic", "upgrade", "head"]

FROM python-deps-install AS server

RUN addgroup --system app && \
    adduser --system --ingroup app app && \
    mkdir -p /app/.ssh && \
    chmod 700 /app/.ssh && \
    chown -R app:app /app/.ssh

COPY ./app /opt/postgresql-managed-service/app
COPY ./keys/servers/ssh_key /app/.ssh/id_rsa
COPY ./keys/servers/ssh_key.pub /app/.ssh/id_rsa.pub
COPY ./keys /opt/postgresql-managed-service/keys

RUN chmod 600 /app/.ssh/id_rsa && \
    chown -R app:app /app/.ssh/id_rsa /app/.ssh/id_rsa.pub /opt/postgresql-managed-service

USER app

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0"]

FROM python-deps-install AS ansible-prebuild

RUN apt-get update && \
    apt-get install -y sudo && \
    rm -rf /var/lib/apt/lists/*

# TODO когда Иван запушит плейбук дописать

FROM python-deps-install AS terraform

RUN apt-get update && \
    apt-get install -y ansible wget gnupg lsb-release && \
    wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && \
    apt-get install -y terraform && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --system terraform && \
    adduser --system --ingroup terraform terraform && \
    mkdir -p /home/terraform/.ssh && \
    chmod 700 /home/terraform/.ssh && \
    chown -R terraform:terraform /home/terraform

# Python приложение (кроме api) 
COPY ./app/config.py /opt/postgresql-managed-service/app/config.py
COPY ./app/run_dramatiq.py /opt/postgresql-managed-service/app/run_dramatiq.py
COPY ./app/src/database /opt/postgresql-managed-service/app/src/database
COPY ./app/src/tasks /opt/postgresql-managed-service/app/src/tasks

# .terraformrc чтобы скачивать providers с яндекс зеркал
COPY ./terraform/.terraformrc /home/terraform/.terraformrc

ENV TF_CLI_CONFIG_FILE=/home/terraform/.terraformrc

# SSH ключи для доступа к создаваемым ВМ
COPY ./keys/servers/ssh_key /home/terraform/.ssh/id_rsa
COPY ./keys/servers/ssh_key.pub /home/terraform/.ssh/id_rsa.pub

# Шаблоны для terraform
COPY ./terraform/template /opt/postgresql-managed-service/terraform/template

# Ansible плейбуки для настройки ВМ (TODO когда Иван запушит плейбук дописать)
COPY ./ansible/vm /opt/postgresql-managed-service/ansible/vm

RUN chmod 600 /home/terraform/.ssh/id_rsa && \
    chown -R terraform:terraform /home/terraform/.ssh /home/terraform/.terraformrc /opt/postgresql-managed-service

USER terraform

CMD ["python", "/opt/postgresql-managed-service/app/run_dramatiq.py", "app.src.tasks.create_vm_task", "--queues", "terraform_queue", "--threads", "1"]

FROM hashicorp/vault:1.21 AS vault

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

CMD sh -c 'vault server -config=/vault/config/config-dev.hcl & VAULT_PID=$!; sleep 15; export VAULT_ADDR=http://127.0.0.1:8200; if vault operator init -status 2>&1 | grep -q "not initialized"; then vault operator init -key-shares=5 -key-threshold=3 -format=json > /vault/init/vault-init.json; chmod 600 /vault/init/vault-init.json; KEY1=$(jq -r ".unseal_keys_b64[0]" /vault/init/vault-init.json); KEY2=$(jq -r ".unseal_keys_b64[1]" /vault/init/vault-init.json); KEY3=$(jq -r ".unseal_keys_b64[2]" /vault/init/vault-init.json); vault operator unseal "$KEY1"; vault operator unseal "$KEY2"; vault operator unseal "$KEY3"; ROOT_TOKEN=$(jq -r ".root_token" /vault/init/vault-init.json); export VAULT_TOKEN="$ROOT_TOKEN"; echo "$ROOT_TOKEN" > /vault/token; chmod 644 /vault/token; chown vault:vault /vault/token; vault secrets enable -version=2 -path=secret kv || true; vault policy write terraform /vault/policies/terraform-policy.hcl || true; vault auth enable approle || true; vault audit enable file file_path=/vault/logs/audit.log || true; fi; if vault status | grep -q "Sealed.*true"; then KEY1=$(jq -r ".unseal_keys_b64[0]" /vault/init/vault-init.json); KEY2=$(jq -r ".unseal_keys_b64[1]" /vault/init/vault-init.json); KEY3=$(jq -r ".unseal_keys_b64[2]" /vault/init/vault-init.json); vault operator unseal "$KEY1"; vault operator unseal "$KEY2"; vault operator unseal "$KEY3"; fi; echo "Vault готов!"; echo "UI: http://localhost:8200/ui"; echo "СОХРАНИТЕ файл /vault/init/vault-init.json!"; wait $VAULT_PID'