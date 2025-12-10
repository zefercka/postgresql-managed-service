FROM python:3.13-slim AS base

RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/postgresql-managed-service


FROM base AS python-deps-install

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python-deps-install AS final

COPY ./app /opt/postgresql-managed-service/app

RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
COPY ./keys/servers/ssh_key /root/.ssh/id_rsa
COPY ./keys/servers/ssh_key.pub /root/.ssh/id_rsa.pub
RUN chmod 600 /root/.ssh/id_rsa

COPY ./keys /opt/postgresql-managed-service/keys

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0"]