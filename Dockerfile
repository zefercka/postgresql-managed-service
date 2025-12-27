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
COPY ./app/load_vault_approle.py /opt/postgresql-managed-service/app/load_vault_approle.py
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

FROM python-deps-install AS ansible

RUN apt-get update && \
    apt-get install -y sudo ansible openssh-client && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --system ansibleuser && \
    adduser --system --ingroup ansibleuser --home /home/ansibleuser --shell /bin/bash ansibleuser

RUN mkdir -p /home/ansibleuser/.ssh && \
    chmod 700 /home/ansibleuser/.ssh && \
    chown ansibleuser:ansibleuser /home/ansibleuser/.ssh

COPY ./keys/servers/ssh_key /home/ansibleuser/.ssh/id_rsa

COPY ./app/config.py /opt/postgresql-managed-service/app/__init__.py
COPY ./app/config.py /opt/postgresql-managed-service/app/config.py
COPY ./app/run_dramatiq.py /opt/postgresql-managed-service/app/run_dramatiq.py
COPY ./app/load_vault_approle.py /opt/postgresql-managed-service/app/load_vault_approle.py
COPY ./app/src/database /opt/postgresql-managed-service/app/src/database
COPY ./app/src/tasks /opt/postgresql-managed-service/app/src/tasks
COPY ./app/src/dependency/helpers.py /opt/postgresql-managed-service/app/src/dependency/helpers.py
COPY ./app/src/dependency/vault.py /opt/postgresql-managed-service/app/src/dependency/vault.py

RUN chmod 600 /home/ansibleuser/.ssh/id_rsa && \
    chown ansibleuser:ansibleuser /home/ansibleuser/.ssh/id_rsa && \
    chown -R ansibleuser:ansibleuser /opt/postgresql-managed-service

USER ansibleuser

CMD ["python", "-m", "app.run_dramatiq", "app.src.tasks.create_cluster_user_task", "--queues", "ansible_queue", "--threads", "8"]

FROM python-deps-install AS terraform

RUN apt-get update && \
    apt-get install -y ansible wget gnupg lsb-release openssh-client sshpass && \
    wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && \
    apt-get install -y terraform && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --system terraform && \
    adduser --system --ingroup terraform --home /home/terraform terraform && \
    mkdir -p /home/terraform/.ssh && \
    chmod 700 /home/terraform/.ssh && \
    chown -R terraform:terraform /home/terraform

# Python приложение (кроме api) 
COPY ./app/config.py /opt/postgresql-managed-service/app/config.py
COPY ./app/run_dramatiq.py /opt/postgresql-managed-service/app/run_dramatiq.py
COPY ./app/load_vault_approle.py /opt/postgresql-managed-service/app/load_vault_approle.py
COPY ./app/src/database /opt/postgresql-managed-service/app/src/database
COPY ./app/src/tasks /opt/postgresql-managed-service/app/src/tasks
COPY ./app/src/dependency/helpers.py /opt/postgresql-managed-service/app/src/dependency/helpers.py
COPY ./app/src/dependency/vault.py /opt/postgresql-managed-service/app/src/dependency/vault.py

# .terraformrc чтобы скачивать providers с яндекс зеркал
COPY ./terraform/.terraformrc /home/terraform/.terraformrc

ENV TF_CLI_CONFIG_FILE=/home/terraform/.terraformrc
ENV HOME=/home/terraform
ENV ANSIBLE_LOCAL_TEMP=/home/terraform/.ansible/tmp
ENV PYTHONPATH=/opt/postgresql-managed-service

# SSH ключи для доступа к создаваемым ВМ
COPY ./keys/servers/ssh_key /home/terraform/.ssh/id_rsa
COPY ./keys/servers/ssh_key.pub /home/terraform/.ssh/id_rsa.pub

# Шаблоны для terraform
COPY ./terraform/template /opt/postgresql-managed-service/terraform/template

# PowerShell скрипты для terraform
COPY ./terraform/scripts /opt/postgresql-managed-service/terraform/scripts

# Ansible плейбуки для настройки ВМ (копировать только нужные)
COPY ./ansible /opt/postgresql-managed-service/ansible

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
             /vault/logs \
             /vault/approle && \
    chown -R vault:vault /vault && \
    chmod 755 /vault/data /vault/certs /vault/init /vault/logs /vault/approle

COPY vault/config-dev.hcl /vault/config/config-dev.hcl
COPY vault/policies/*.hcl /vault/policies/
COPY vault/entrypoint.sh /vault/scripts/entrypoint.sh

RUN chown -R vault:vault /vault && \
    chmod 755 /vault/scripts && \
    chmod 755 /vault/scripts/entrypoint.sh && \
    chmod 755 /vault/init && \
    chmod 755 /vault/logs && \
    chmod 755 /vault/data

# Используем jq для парсинга JSON
RUN apk add --no-cache jq

ENTRYPOINT ["/vault/scripts/entrypoint.sh"]