FROM python:3.12-slim

# Установим SSH-сервер
RUN apt update && apt install -y openssh-server sudo && rm -rf /var/lib/apt/lists/*

# Создадим пользователя
RUN useradd -m -s /bin/bash ansibleuser && \
    echo 'ansibleuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Создадим папку для SSH
RUN mkdir -p /home/ansibleuser/.ssh && \
    chown ansibleuser:ansibleuser /home/ansibleuser/.ssh && \
    chmod 700 /home/ansibleuser/.ssh

# Копируем твой публичный ключ внутрь контейнера
# Предположим, твой публичный ключ находится рядом с Dockerfile как id_rsa.pub
COPY keys/servers/ssh_key /home/ansibleuser/.ssh/authorized_keys

RUN chown ansibleuser:ansibleuser /home/ansibleuser/.ssh/authorized_keys && \
    chmod 600 /home/ansibleuser/.ssh/authorized_keys

# Разрешаем root логин по SSH (опционально)
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

CMD ["tail", "-f", "/dev/null"]