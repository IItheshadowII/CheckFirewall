# FirewallMonitor Agent
# 
# This script checks the status of Windows Firewall profiles and sends a heartbeat to the central server.
# If any active profile is disabled, it reports a "Risk" status (firewall_status = $false).

param (
    [string]$ServerUrl = "http://localhost:8000/api/heartbeat",
    [string]$ApiKey = "change-me-please",
    [string]$Hostname = $env:COMPUTERNAME
)

# --- Configuration ---
$LogFile = "C:\ProgramData\FirewallMonitor\agent.log"
$ErrorActionPreference = "Stop"

# Ensure log directory exists
if (-not (Test-Path "C:\ProgramData\FirewallMonitor")) {
    New-Item -ItemType Directory -Path "C:\ProgramData\FirewallMonitor" -Force | Out-Null
}

function Write-Log {
    param ([string]$Message)
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$TimeStamp - $Message" | Out-File -FilePath $LogFile -Append
}

function Get-IPv4Address {
    try {
        $ip = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias * -ConnectionState Connected | Where-Object { $_.PrefixOrigin -ne 'WellKnown' } | Select-Object -First 1).IPAddress
        return $ip
    }
    catch {
        return "Unknown"
    }
}

try {
    # 1. Get Firewall Profiles
    $profiles = Get-NetFirewallProfile
    
    $profilesStatus = @{}
    $overallStatus = $true
    
    foreach ($p in $profiles) {
        $isEnabled = $p.Enabled -eq "True" -or $p.Enabled -eq 1
        $profilesStatus[$p.Name] = $isEnabled
        
        # Logic: If a profile is disabled, is it a risk?
        # Usually checking all profiles is strict.
        if (-not $isEnabled) {
            $overallStatus = $false
        }
    }

    # 2. Prepare Payload
    $payload = @{
        hostname        = $Hostname
        ip_address      = Get-IPv4Address
        firewall_status = $overallStatus
        profiles_status = $profilesStatus
    }
    
    $jsonPayload = $payload | ConvertTo-Json -Depth 5

    # 3. Send Heartbeat
    $headers = @{
        "X-API-KEY"    = $ApiKey
        "Content-Type" = "application/json"
    }

    Invoke-RestMethod -Uri $ServerUrl -Method Post -Headers $headers -Body $jsonPayload -TimeoutSec 10
    
    Write-Log "Heartbeat sent successfully. Status: $overallStatus"

}
catch {
    Write-Log "ERROR: $_"
    # Optional: Log to Event Viewer
    # Write-EventLog ...
    exit 1
}
