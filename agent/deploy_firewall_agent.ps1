<#
Deploy Firewall Monitor Agent (Endpoint Central friendly)

- Copia el agente a C:\ProgramData\FirewallMonitor\firewall_monitor.ps1
- Crea/actualiza una tarea programada que corre como SYSTEM cada N minutos y al iniciar
- Idempotente: se puede ejecutar múltiples veces sin romper nada

Parámetros principales:
- ServerIP / ServerUrl: a qué backend mandar el heartbeat
- ApiKey: debe coincidir con API_KEY del backend
- IntervalMinutes: cada cuántos minutos reporta el agente

Exit codes:
  0 = OK
  1 = Error
#>

[CmdletBinding()]
param(
  # Si querés usar IP (se usa solo si no pasás ServerUrl)
  [string]$ServerIP = "10.127.1.156",

  # O si preferís pasar la URL completa desde Endpoint Central
  [string]$ServerUrl = "",

  # Debe coincidir con API_KEY del backend
  [string]$ApiKey = "change-me-please",

  # Intervalo en minutos entre heartbeats
  [int]$IntervalMinutes = 5,

  [string]$InstallDir = "C:\\ProgramData\\FirewallMonitor",

  [string]$TaskName = "FirewallMonitorAgent"
)

$ErrorActionPreference = "Stop"

function Write-DeployLog {
  param([string]$Message)
  $log = Join-Path $InstallDir "deploy.log"
  $ts  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  try {
    if (!(Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null }
    Add-Content -Path $log -Value "[$ts] $Message"
  } catch {
    # Si no se puede loguear, igual seguimos
  }
}

try {
  # -------------------------
  # 1) Resolver ServerUrl
  # -------------------------
  if ([string]::IsNullOrWhiteSpace($ServerUrl)) {
    # Por defecto apuntamos al backend Docker en el puerto 8000
    $ServerUrl = "http://$ServerIP`:8000/api/heartbeat"
  }

  if ($IntervalMinutes -lt 1) { throw "IntervalMinutes no puede ser < 1" }

  Write-DeployLog "Iniciando deploy. ServerUrl=$ServerUrl IntervalMinutes=$IntervalMinutes TaskName=$TaskName"

  # -------------------------
  # 2) Crear carpeta destino
  # -------------------------
  if (!(Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Write-DeployLog "Creada carpeta: $InstallDir"
  }

  # -------------------------
  # 3) Escribir agente (firewall_monitor.ps1)
  # -------------------------
  $agentPath = Join-Path $InstallDir "firewall_monitor.ps1"
  $agentLog  = Join-Path $InstallDir "agent.log"

  $agentScript = @"
# FirewallMonitor Agent
# - Chequea perfiles de Windows Firewall
# - Envía heartbeat a servidor central
# - Log: $agentLog

param(
  [string]`$ServerUrl,
  [string]`$ApiKey,
  [string]`$Hostname = `$env:COMPUTERNAME
)

`$ErrorActionPreference = "Stop"
`$LogFile = "$agentLog"

function Write-Log {
  param([string]`$Message)
  try {
    `$dir = Split-Path -Parent `$LogFile
    if (!(Test-Path `$dir)) { New-Item -ItemType Directory -Path `$dir -Force | Out-Null }
    `$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path `$LogFile -Value "[`$ts] `$Message"
  } catch { }
}

function Get-IPv4Address {
  try {
    # Intento principal: usar Get-NetIPAddress filtrando direcciones válidas
    `$candidates = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
      Where-Object {
        `$_.IPAddress -and
        `$_.IPAddress -notlike '169.254*' -and
        `$_.IPAddress -notlike '127.*'
      } |
      Sort-Object -Property PrefixLength -Descending

    `$ip = (`$candidates | Select-Object -First 1).IPAddress
    if (`$ip) { return `$ip }
  } catch {
    # Ignorar y probar fallback
  }

  # Fallback: parsear salida de ipconfig por si Get-NetIPAddress no está disponible
  try {
    `$raw = ipconfig | Select-String -Pattern 'IPv4 Address.*?:\s*([0-9\.]+)' -AllMatches
    if (`$raw -and `$raw.Matches.Count -gt 0) {
      return `$raw.Matches[0].Groups[1].Value
    }
  } catch { }

  return "Unknown"
}

try {
  if ([string]::IsNullOrWhiteSpace(`$ServerUrl)) { throw "ServerUrl vacío" }
  if ([string]::IsNullOrWhiteSpace(`$ApiKey)) { throw "ApiKey vacío" }

  # Traer estado de perfiles Domain / Private / Public
  `$profiles = Get-NetFirewallProfile | Select-Object Name, Enabled

  `$profilesStatus = @{}
  `$anyDisabled = `$false
  foreach (`$p in `$profiles) {
    `$isEnabled = (`$p.Enabled -eq "True" -or `$p.Enabled -eq 1 -or `$p.Enabled -eq `$true)
    `$profilesStatus[`$p.Name] = `$isEnabled
    if (-not `$isEnabled) { `$anyDisabled = `$true }
  }

  `$ipChosen = Get-IPv4Address

  `$payload = [ordered]@{
    hostname        = `$Hostname
    ip_address      = `$ipChosen
    firewall_status = (-not `$anyDisabled)
    profiles_status = `$profilesStatus
  }

  `$jsonPayload = (`$payload | ConvertTo-Json -Depth 6)

  `$headers = @{
    "X-API-KEY"    = `$ApiKey
    "Content-Type" = "application/json"
  }

  Invoke-RestMethod -Uri `$ServerUrl -Method Post -Headers `$headers -Body `$jsonPayload -TimeoutSec 10 | Out-Null
  Write-Log "Heartbeat OK. IP=`$ipChosen Disabled=`$anyDisabled"
  exit 0
}
catch {
  Write-Log "ERROR: `$($_.Exception.Message)"
  exit 1
}
"@

  # Guardar (si cambió, lo pisa igual)
  Set-Content -Path $agentPath -Value $agentScript -Encoding UTF8
  Write-DeployLog "Agente escrito en: $agentPath"

  # -------------------------
  # 4) Crear/Actualizar tarea programada
  # -------------------------
  # Acción: PowerShell.exe -ExecutionPolicy Bypass -File "agentPath" -ServerUrl "..." -ApiKey "..."
  $psArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$agentPath`"",
    "-ServerUrl", "`"$ServerUrl`"",
    "-ApiKey", "`"$ApiKey`""
  ) -join " "

  $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument $psArgs

  # Trigger repetitivo: arranca en 1 minuto y repite cada N minutos por muchos años
  $now = (Get-Date).AddMinutes(1)
  $triggerRepeat = New-ScheduledTaskTrigger -Once -At $now `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

  # Trigger al inicio (por si el server se reinicia, no esperás al próximo tick)
  $triggerStartup = New-ScheduledTaskTrigger -AtStartup

  $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

  $settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
    -Hidden

  # Crear/Actualizar
  $task = New-ScheduledTask -Action $action -Trigger @($triggerRepeat, $triggerStartup) -Principal $principal -Settings $settings

  Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
  Write-DeployLog "Tarea registrada/actualizada: $TaskName"

  # -------------------------
  # 5) Disparar una corrida inmediata (opcional)
  # -------------------------
  try {
    Start-ScheduledTask -TaskName $TaskName
    Write-DeployLog "Tarea iniciada manualmente para test rápido."
  } catch {
    Write-DeployLog "No se pudo iniciar manualmente la tarea (no es fatal): $($_.Exception.Message)"
  }

  Write-DeployLog "Deploy finalizado OK."
  exit 0
}
catch {
  Write-DeployLog "DEPLOY ERROR: $($_.Exception.Message)"
  exit 1
}
