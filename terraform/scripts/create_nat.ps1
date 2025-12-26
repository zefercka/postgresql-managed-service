# Скрипт для создания NAT сети с поддержкой выхода в интернет
param(
    [string]$NatName = "InternalNatNetwork",
    [string]$InternalIPInterfaceAddressPrefix = "192.168.100.0/24"
)

$existingNat = Get-NetNat -Name $NatName -ErrorAction SilentlyContinue

if (-not $existingNat) {
    Write-Host "Creating NAT network $NatName with prefix $InternalIPInterfaceAddressPrefix"
    try {
        New-NetNat -Name $NatName -InternalIPInterfaceAddressPrefix $InternalIPInterfaceAddressPrefix -ErrorAction Stop
        Write-Host "NAT network created successfully"
    } catch {
        Write-Host "Warning: Could not create NAT (may already exist): $($_.Exception.Message)"
        # Проверяем еще раз после ошибки
        $existingNat = Get-NetNat -Name $NatName -ErrorAction SilentlyContinue
        if ($existingNat) {
            Write-Host "NAT network $NatName exists after retry"
        }
    }
} else {
    Write-Host "NAT network $NatName already exists"
}

# Включаем IP Forwarding для маршрутизации трафика
Write-Host "Enabling IP Forwarding..."
try {
    Set-NetIPInterface -InterfaceAlias "vEthernet (DMZ)" -Forwarding Enabled -ErrorAction Stop
    Write-Host "IP Forwarding enabled"
} catch {
    Write-Host "Warning: Could not enable IP Forwarding: $($_.Exception.Message)"
}

# Проверяем и настраиваем DNS для NAT сети (только для Windows Server)
Write-Host "Checking DNS configuration..."
$dnsService = Get-Service -Name "DNS" -ErrorAction SilentlyContinue
if ($dnsService -and $dnsService.Status -eq "Running") {
    # DNS Server запущен, пытаемся настроить forwarders
    try {
        Add-DnsServerForwarder -IPAddress "8.8.8.8" -ErrorAction Stop
        Add-DnsServerForwarder -IPAddress "1.1.1.1" -ErrorAction Stop
        Write-Host "DNS forwarders configured"
    } catch {
        Write-Host "Note: DNS forwarders not configured (may already exist or not available)"
    }
} else {
    Write-Host "DNS Server not running (this is normal for client Windows)"
}
