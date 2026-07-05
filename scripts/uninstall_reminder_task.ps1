param(
    [string]$TaskName = "EPux Vocabulary Reminder"
)

$ErrorActionPreference = "Stop"
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed scheduled task: $TaskName"
}
catch {
    Write-Host "Scheduled task was not removed or did not exist."
}

$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "$TaskName.lnk"
if (Test-Path $ShortcutPath) {
    Remove-Item -LiteralPath $ShortcutPath -Force
    Write-Host "Removed Startup shortcut: $ShortcutPath"
}
