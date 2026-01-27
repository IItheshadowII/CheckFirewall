# Installer Snippet
# Run as Administrator to schedule the task

$# Configura aquí la IP LAN del servidor (reemplaza por la IP real)
$ServerIP = "192.168.1.100"
$ApiKey = "change-me-please"
$AgentPath = "C:\Path\To\agent\firewall_monitor.ps1"

# Construye la URL completa del endpoint del servidor
$ServerUrl = "http://$ServerIP:8000/api/heartbeat"

# Argumentos que se pasarán al script del agente
$Arguments = "-ExecutionPolicy Bypass -File `"$AgentPath`" -ServerUrl `"$ServerUrl`" -ApiKey `"$ApiKey`""

$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden

Register-ScheduledTask -TaskName "FirewallMonitorAgent" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force

Write-Host "Task Scheduled Successfully. ServerUrl=$ServerUrl"
