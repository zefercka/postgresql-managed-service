FROM python:3.12-slim AS base

RUN apt-get update && \
    apt-get install -y ansible wget gnupg lsb-release && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/postgresql-managed-service

FROM base AS terraform-install

RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && apt-get install -y terraform

COPY ./terraform/.terraformrc /root/.terraformrc

FROM terraform-install AS python-deps-install

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python-deps-install AS final
# Там все файлы не нужны, взять только то, что нужно
COPY ./app /opt/postgresql-managed-service/app

RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
COPY ./keys/servers/ssh_key /root/.ssh/id_rsa
COPY ./keys/servers/ssh_key.pub /root/.ssh/id_rsa.pub
RUN chmod 600 /root/.ssh/id_rsa

CMD ["python", "app/run_dramatiq.py", "app.src.tasks.create_vm_task", "--queue", "default", "--threads", "1"]
# CMD ["tail", "-f", "/dev/null"]