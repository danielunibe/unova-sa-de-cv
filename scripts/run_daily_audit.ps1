$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$serverScript = Join-Path $workspace "scripts\unova_server.py"

try {
    Invoke-RestMethod `
        -Uri "http://127.0.0.1:4173/api/scan" `
        -Method Post `
        -TimeoutSec 10 | Out-Null
}
catch {
    $python = (Get-Command python.exe -ErrorAction Stop).Source
    & $python $serverScript --scan-once
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
