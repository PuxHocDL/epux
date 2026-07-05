param(
    [string]$TaskName = "EPux Vocabulary Reminder"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = (Get-Command python).Source
$Pythonw = Join-Path (Split-Path $Python -Parent) "pythonw.exe"
if (-not (Test-Path $Pythonw)) {
    $Pythonw = $Python
}

$Action = New-ScheduledTaskAction `
    -Execute $Python `
    -Argument "-m epux remind --daemon --window" `
    -WorkingDirectory $RepoRoot

$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Principal $Principal `
        -Description "EPux local vocabulary review reminders" `
        -Force | Out-Null

    Write-Host "Installed scheduled task: $TaskName"
    Write-Host "It will run: python -m epux remind --daemon --window"
}
catch {
    $Startup = [Environment]::GetFolderPath("Startup")
    $ShortcutPath = Join-Path $Startup "$TaskName.lnk"
    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $Pythonw
    $Shortcut.Arguments = "-m epux remind --daemon --window"
    $Shortcut.WorkingDirectory = $RepoRoot
    $Shortcut.Description = "EPux local vocabulary review reminders"
    $Shortcut.Save()

    Write-Host "Task Scheduler denied access, installed Startup shortcut instead:"
    Write-Host $ShortcutPath
    Write-Host "It will run: pythonw -m epux remind --daemon --window"
}
