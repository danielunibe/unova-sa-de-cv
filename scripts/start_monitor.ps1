$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$serverScript = Join-Path $workspace "scripts\unova_server.py"

function Test-UnovaPort {
    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $task = $client.ConnectAsync("127.0.0.1", 4173)
        if (-not $task.Wait(700)) {
            $client.Dispose()
            return $false
        }
        $connected = $client.Connected
        $client.Dispose()
        return $connected
    }
    catch {
        return $false
    }
}

if (Test-UnovaPort) {
    exit 0
}

$python = (Get-Command python.exe -ErrorAction Stop).Source
$pythonw = Join-Path (Split-Path -Parent $python) "pythonw.exe"
if (-not (Test-Path -LiteralPath $pythonw)) {
    $pythonw = $python
}

Start-Process -FilePath $pythonw `
    -ArgumentList @("`"$serverScript`"") `
    -WorkingDirectory $workspace `
    -WindowStyle Hidden

$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline -and -not (Test-UnovaPort)) {
    Start-Sleep -Milliseconds 400
}

if (-not (Test-UnovaPort)) {
    throw "El servidor UNOVA no respondió en 127.0.0.1:4173."
}
