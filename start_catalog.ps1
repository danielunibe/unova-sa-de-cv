$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $root "scripts\start_monitor.ps1")
Start-Process "http://127.0.0.1:4173/?v=4"
