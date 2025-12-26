param(
    [string]$InternalIP,
    [string]$OutputFile = "C:\Temp\nat_ports.txt"
)

$NatName = "InternalNatNetwork"
$StartPort = 20000
$Protocol = "TCP"

function Find-FreePort {
    param([int]$Start)

    for ($p = $Start; $p -le 65535; $p++) {

        $portFree = -not (Test-NetConnection `
            -ComputerName 127.0.0.1 `
            -Port $p `
            -WarningAction SilentlyContinue
        ).TcpTestSucceeded

        $natFree = -not (
            Get-NetNatStaticMapping `
                -NatName $NatName `
                -ErrorAction SilentlyContinue |
            Where-Object { $_.ExternalPort -eq $p -and $_.Protocol -eq $Protocol }
        )

        if ($portFree -and $natFree) {
            return $p
        }
    }

    throw "No free ports"
}

function Add-NatPort {
    param(
        [int]$ExternalPort,
        [int]$InternalPort
    )

    $exists = Get-NetNatStaticMapping `
        -NatName $NatName `
        -ErrorAction SilentlyContinue |
        Where-Object {
            $_.ExternalPort -eq $ExternalPort -and
            $_.Protocol -eq $Protocol
        }

    if ($exists) {
        Write-Host "Port forwarding for port $ExternalPort already exists. Skipping."
        return
    }

    Write-Host "Creating NAT port forwarding: $ExternalPort -> $InternalIP`:$InternalPort"

    Add-NetNatStaticMapping `
        -NatName $NatName `
        -Protocol $Protocol `
        -ExternalIPAddress '0.0.0.0' `
        -ExternalPort $ExternalPort `
        -InternalIPAddress $InternalIP `
        -InternalPort $InternalPort

    Write-Host "Port forwarding created successfully"
}

$sshPort = Find-FreePort -Start $StartPort
$pgPort  = Find-FreePort -Start ($sshPort + 1)

Write-Host "Found free port for SSH: $sshPort"
Write-Host "Found free port for PostgreSQL: $pgPort"

Add-NatPort -ExternalPort $sshPort -InternalPort 22
Add-NatPort -ExternalPort $pgPort  -InternalPort 5432

Set-Content `
    -Path $OutputFile `
    -Value "SSH=$sshPort;PG=$pgPort"
