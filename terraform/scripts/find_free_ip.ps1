# Скрипт для поиска свободного IP-адреса с механизмом блокировки
param(
    [string]$OutputFile = "C:\Temp\free_ip.txt"
)

$NetworkPrefix = "192.168.100"
$StartRange = 20
$EndRange = 254
$LockDir = "C:\Temp\ip_locks"
$LockTimeoutMinutes = 5

# Создание необходимых директорий
if (!(Test-Path -Path 'C:\Temp' -PathType Container)) {
    New-Item -ItemType Directory -Path 'C:\Temp' -Force | Out-Null
}

if (!(Test-Path -Path $LockDir -PathType Container)) {
    New-Item -ItemType Directory -Path $LockDir -Force | Out-Null
}

Write-Host "Starting search for free IP address in range $NetworkPrefix.$StartRange - $NetworkPrefix.$EndRange"

# Очистка устаревших блокировок перед поиском
if (Test-Path $LockDir) {
    Get-ChildItem -Path $LockDir -File | ForEach-Object {
        $fileAge = (Get-Date) - $_.CreationTime
        if ($fileAge.TotalMinutes -gt $LockTimeoutMinutes) {
            Write-Host "Removing stale lock file: $($_.Name)"
            Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        }
    }
}

$candidate_ips = $StartRange..$EndRange | ForEach-Object { $NetworkPrefix + "." + $_ }

foreach ($ip in $candidate_ips) {
    $lockFile = Join-Path $LockDir ($ip -replace '\.', '_')
    
    # Пропускаем IP, если он уже заблокирован
    if (Test-Path $lockFile) {
        $fileAge = (Get-Date) - (Get-Item $lockFile).CreationTime
        if ($fileAge.TotalMinutes -le $LockTimeoutMinutes) {
            Write-Host "IP $ip is locked, skipping"
            continue
        } else {
            # Удаляем устаревшую блокировку
            Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Проверяем, что IP свободен (не отвечает на ping)
    if (-not (Test-Connection -ComputerName $ip -Count 1 -Quiet -ErrorAction SilentlyContinue)) {
        try {
            # Создаем файл-блокировку с эксклюзивным доступом
            $stream = [System.IO.File]::Open($lockFile, 'CreateNew', 'Write', 'None')
            $writer = New-Object System.IO.StreamWriter($stream)
            $writer.WriteLine((Get-Date).ToString())
            $writer.Close()
            $stream.Close()
            
            Write-Host "Found free IP: $ip (locked)" -ForegroundColor Green
            Set-Content -Path $OutputFile -Value $ip
            Write-Output $ip
            exit 0
        }
        catch {
            # Другой процесс успел заблокировать этот IP, продолжаем поиск
            Write-Host "IP $ip was locked by another process, continuing search"
            continue
        }
    }
}

Write-Host "No free IP found in range $NetworkPrefix.$StartRange - $NetworkPrefix.$EndRange" -ForegroundColor Red
throw "Failed to find a free IP address"
