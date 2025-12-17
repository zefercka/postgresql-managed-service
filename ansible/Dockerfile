FROM python:3.12-slim

# Установим SSH-сервер
RUN apt update && apt install -y openssh-server sudo ansible && \
    rm -rf /var/lib/apt/lists/*

# Создадим пользователя
RUN useradd -m -s /bin/bash ansibleuser && \
    echo 'ansibleuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Создадим папку для SSH
RUN mkdir -p /home/ansibleuser/.ssh && \
    chown ansibleuser:ansibleuser /home/ansibleuser/.ssh && \
    chmod 700 /home/ansibleuser/.ssh

# Копируем твой публичный ключ внутрь контейнера
# Предположим, твой публичный ключ находится рядом с Dockerfile как id_rsa.pub
COPY keys/servers/ssh_key /home/ansibleuser/.ssh/id_rsa

RUN chown ansibleuser:ansibleuser /home/ansibleuser/.ssh/id_rsa && chmod 600 /home/ansibleuser/.ssh/id_rsa

RUN eval $(ssh-agent) && ssh-add /home/ansibleuser/.ssh/id_rsa

CMD ["tail", "-f", "/dev/null"]