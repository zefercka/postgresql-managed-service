# Скрипт для освобождения блокировки IP адреса
param(
    [string]$IPAddress
)

$LockDir = "C:\Temp\ip_locks"

if (-not $IPAddress) {
    # If IP not provided, read from file
    if (Test-Path "C:\Temp\free_ip.txt") {
        $IPAddress = Get-Content "C:\Temp\free_ip.txt"
    } else {
        Write-Host "IP address not specified and file C:\Temp\free_ip.txt not found"
        exit 1
    }
}

$lockFile = Join-Path $LockDir ($IPAddress -replace '\.', '_')

if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "Lock for IP $IPAddress removed successfully"
} else {
    Write-Host "Lock for IP $IPAddress not found"
}
