# Vault Server Configuration (Dev Mode с TLS отключен для упрощения)
# Для production обязательно включить TLS!

# Настройка хранилища данных
storage "file" {
  path = "/vault/data"
}

# Настройка API listener БЕЗ TLS (только для dev/testing)
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_disable   = 1
}

# API адрес
api_addr = "http://vault:8200"

# UI включен для удобства администрирования
ui = true

# Максимальное время аренды токенов (30 дней)
max_lease_ttl = "720h"
# Стандартное время аренды (7 дней)
default_lease_ttl = "168h"

# Отключение mlock для Docker
disable_mlock = true

# Логирование
log_level = "Info"
log_format = "json"

# Telemetry для мониторинга
telemetry {
  disable_hostname = false
  prometheus_retention_time = "30s"
}
