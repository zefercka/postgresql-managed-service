# PostgreSQL Managed Service

### Настройка ВМ прообраза
#### 1. Скачать готовый диск

#### 2. Создать диск самостоятельно

##### Создание ВМ в Hyper-V
1. Скачайте `.iso` образ для UbuntuServer (ubuntu-24.04.3-live-server-amd64.iso)
2. Установить SSH Server 
```bash
sudo apt install -y openserver-ssh
```
3. Добавить ssh ключи (на всех ВМ используется один и тот же ключ)


## Запуск приложения
Выполните `docker-compose up`

### Настройка Vault
1. Чтобы узнать токен для Vault -- выполните: 
```bash
docker exec ms-vault cat /vault/token-storage/root-token
```

2. Перейдите на `http://localhost:8200/ui/vault/auth`

3. Введите токен полученный в 1 пункте