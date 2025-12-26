# Скрипт для проброса порта на базовый IP для первого подключения ansible

param(
    [string]$InternalIP
)

$natName = 'InternalNatNetwork'
$externalPort = 22222
$internalPort = 22

$exists = Get-NetNatStaticMapping -NatName $natName -ErrorAction SilentlyContinue | Where-Object { $_.ExternalPort -eq $externalPort -and $_.Protocol -eq 'TCP' }

if ($exists) {
    Write-Host 'Port forwarding already exists. Skipping.' 
} else {
    Write-Host 'Creating NAT port forward for port', $port, '...'
    Add-NetNatStaticMapping -NatName $natName -Protocol TCP -ExternalIPAddress '0.0.0.0' -ExternalPort $externalPort -InternalIPAddress $InternalIP -InternalPort $internalPort
    Write-Host 'Port forward created.'
}
