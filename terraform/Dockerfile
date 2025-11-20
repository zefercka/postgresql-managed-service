FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y ansible && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/postgresql-managed-service

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Там все файлы не нужны, взять только то, что нужно
COPY ./app /opt/postgresql-managed-service/app

RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
COPY keys/servers/ssh_key /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys

COPY ./terraform/.terraform.rc /root/.terraform.rc

# CMD ["python app/run_dramatiq.py app.src.tasks.create_vm_task --queue default --threads 1"]
CMD ["tail", "-f", "/dev/null"]