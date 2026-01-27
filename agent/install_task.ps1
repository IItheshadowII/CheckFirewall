# Installer Snippet
# Run as Administrator to schedule the task

$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File ""C:\Path\To\agent\firewall_monitor.ps1"""
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden

Register-ScheduledTask -TaskName "FirewallMonitorAgent" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force

Write-Host "Task Scheduled Successfully."
