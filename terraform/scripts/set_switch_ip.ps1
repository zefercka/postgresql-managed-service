# Скрипт для установки IP адреса для внутреннего сетевого свитча

$InterfaceAlias = "vEthernet (DMZ)"
$IPAddress = "192.168.100.1"
$PrefixLength = 24


Start-Sleep -Seconds 5

$existingIP = (Get-NetIPAddress -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -eq $IPAddress })

if (-not $existingIP) {
    Write-Host "Configuring IP address $IPAddress for interface $InterfaceAlias"
    
    # Remove existing IPv4 addresses
     Remove-NetIPAddress -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
    
    # Set new IP
    New-NetIPAddress -IPAddress $IPAddress -PrefixLength $PrefixLength -InterfaceAlias $InterfaceAlias
    
    Write-Host "IP address configured successfully"
} else {
    Write-Host "IP address $IPAddress is already configured for interface $InterfaceAlias"
}
