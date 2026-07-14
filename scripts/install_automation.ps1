$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$startScript = Join-Path $workspace "scripts\start_monitor.ps1"
$dailyScript = Join-Path $workspace "scripts\run_daily_audit.ps1"
$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId $user `
    -LogonType Interactive `
    -RunLevel Limited

$monitorAction = New-ScheduledTaskAction `
    -Execute $powerShell `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$startScript`""
$monitorTrigger = New-ScheduledTaskTrigger -AtLogOn -User $user

Register-ScheduledTask `
    -TaskName "UNOVA Dashboard Monitor" `
    -Description "Inicia el dashboard y monitor local UNOVA al iniciar sesión." `
    -Action $monitorAction `
    -Trigger $monitorTrigger `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

$dailyAction = New-ScheduledTaskAction `
    -Execute $powerShell `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$dailyScript`""
$dailyTrigger = New-ScheduledTaskTrigger -Daily -At "23:30"

Register-ScheduledTask `
    -TaskName "UNOVA Daily Audit" `
    -Description "Solicita la auditoría global diaria UNOVA; se ejecuta al volver a iniciar si se perdió la hora." `
    -Action $dailyAction `
    -Trigger $dailyTrigger `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

Get-ScheduledTask -TaskName "UNOVA Dashboard Monitor", "UNOVA Daily Audit" |
    Select-Object TaskName, State
