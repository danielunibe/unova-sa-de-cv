$ErrorActionPreference = "Stop"
"UNOVA Dashboard Monitor", "UNOVA Daily Audit" | ForEach-Object {
    if (Get-ScheduledTask -TaskName $_ -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $_ -Confirm:$false
    }
}
