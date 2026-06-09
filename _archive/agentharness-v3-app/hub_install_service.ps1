# ============================================================
#  AgentHarness Hub -- Windows Service Installer (Phase 4)
#  Registers hub_server.py as a Windows Service using NSSM
#  (Non-Sucking Service Manager -- free, no pywin32 needed)
#
#  Run as Administrator:
#    powershell.exe -ExecutionPolicy Bypass -File ".agents\agentharness\app\v3\hub_install_service.ps1"
#
#  Options:
#    -Action install   (default) -- install and start service
#    -Action remove    -- stop and remove service
#    -Action restart   -- restart service
#    -Action status    -- show current service status
# ============================================================

param(
    [string]$Action = "install"
)

$ErrorActionPreference = "Continue"

$ServiceName = "AgentHarnessHub"
$DisplayName = "AgentHarness Hub Server"
$Description = "Always-on agent execution server for AgentHarness v3 -- Smith Capital Portfolio"
$ScriptDir   = $PSScriptRoot
$RepoRoot    = (Resolve-Path (Join-Path $ScriptDir "../../../../")).Path.TrimEnd('\')
$VenvPython  = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$HubScript   = Join-Path $ScriptDir "hub_server.py"
$NssmPath    = Join-Path $RepoRoot ".agents\tools\nssm.exe"
$NssmDir     = Split-Path $NssmPath -Parent
$LogDir      = Join-Path $RepoRoot ".agents\data\logs"

Write-Host ""
Write-Host "  [Hub Service] AgentHarness Hub -- Windows Service Manager" -ForegroundColor Cyan
Write-Host "  Action: $Action" -ForegroundColor DarkGray
Write-Host ""

# -- Check admin rights --------------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "  [ERROR] Must run as Administrator to manage Windows Services." -ForegroundColor Red
    Write-Host "          Right-click PowerShell -> 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# -- Download NSSM if not present ----------------------------------------------
if (-not (Test-Path $NssmPath)) {
    Write-Host "  [..] Downloading NSSM (Non-Sucking Service Manager)..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $NssmDir -Force | Out-Null
    $NssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $ZipPath = Join-Path $env:TEMP "nssm.zip"
    try {
        Invoke-WebRequest -Uri $NssmUrl -OutFile $ZipPath -ErrorAction Stop
        Expand-Archive -Path $ZipPath -DestinationPath (Join-Path $env:TEMP "nssm_extracted") -Force
        # Find nssm.exe (64-bit)
        $found = Get-ChildItem -Path (Join-Path $env:TEMP "nssm_extracted") -Recurse -Filter "nssm.exe" |
                 Where-Object { $_.FullName -match "win64" } |
                 Select-Object -First 1
        if (-not $found) {
            $found = Get-ChildItem -Path (Join-Path $env:TEMP "nssm_extracted") -Recurse -Filter "nssm.exe" |
                     Select-Object -First 1
        }
        if ($found) {
            Copy-Item $found.FullName $NssmPath -Force
            Write-Host "  [OK]  NSSM downloaded to $NssmPath" -ForegroundColor Green
        } else {
            throw "nssm.exe not found in archive"
        }
    } catch {
        Write-Host "  [FAIL] Could not download NSSM: $_" -ForegroundColor Red
        Write-Host "         Manual install: download nssm from https://nssm.cc and place nssm.exe at:" -ForegroundColor Yellow
        Write-Host "         $NssmPath" -ForegroundColor DarkGray
        exit 1
    }
}

# ================================================================================
switch ($Action.ToLower()) {

    "install" {
        Write-Host "  [..] Installing Windows Service: $ServiceName" -ForegroundColor Yellow

        # Check if already installed
        $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Host "  [WARN] Service already installed. Use -Action restart or -Action remove first." -ForegroundColor Yellow
            $existing | Format-List Name, Status, StartType
            exit 0
        }

        # Load .env variables for the service environment
        $envFile = Join-Path $RepoRoot ".agents\.env"
        $envVars = @{}
        if (Test-Path $envFile) {
            Get-Content $envFile | ForEach-Object {
                if ($_ -match "^([A-Za-z_][A-Za-z0-9_]*)=(.+)$") {
                    $v = $Matches[2].Trim()
                    if ($v -match "^`$'(.+)'`$") { $v = $Matches[1] }
                    elseif ($v -match "^'(.+)'`$") { $v = $Matches[1] }
                    elseif ($v -match '^"(.+)"`$')  { $v = $Matches[1] }
                    $envVars[$Matches[1].Trim()] = $v
                }
            }
        }

        # Install service via NSSM
        & $NssmPath install $ServiceName $VenvPython $HubScript

        # Configure service
        & $NssmPath set $ServiceName AppDirectory $ScriptDir
        & $NssmPath set $ServiceName DisplayName $DisplayName
        & $NssmPath set $ServiceName Description $Description
        & $NssmPath set $ServiceName Start SERVICE_AUTO_START

        # Logging
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
        & $NssmPath set $ServiceName AppStdout (Join-Path $LogDir "hub-service-stdout.log")
        & $NssmPath set $ServiceName AppStderr (Join-Path $LogDir "hub-service-stderr.log")
        & $NssmPath set $ServiceName AppRotateFiles 1
        & $NssmPath set $ServiceName AppRotateSeconds 86400   # Rotate daily

        # Restart policy: restart after 5s if it crashes
        & $NssmPath set $ServiceName AppRestartDelay 5000

        # Set environment variables from .env
        foreach ($key in $envVars.Keys) {
            & $NssmPath set $ServiceName AppEnvironmentExtra "$key=$($envVars[$key])"
        }

        # Start the service
        Write-Host "  [..] Starting service..." -ForegroundColor Yellow
        Start-Service -Name $ServiceName -ErrorAction SilentlyContinue

        Start-Sleep -Seconds 3

        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -eq "Running") {
            Write-Host "  [OK]  Service installed and running." -ForegroundColor Green
            Write-Host ""
            Write-Host "        REST API : http://localhost:8765/api" -ForegroundColor Cyan
            Write-Host "        WebSocket: ws://localhost:8765/ws" -ForegroundColor Cyan
            Write-Host "        API Docs : http://localhost:8765/docs" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  The Hub will now start automatically when Windows boots." -ForegroundColor Green
        } else {
            Write-Host "  [WARN] Service installed but may not be running yet." -ForegroundColor Yellow
            Write-Host "         Check logs: $LogDir\hub-service-stderr.log" -ForegroundColor DarkGray
        }
    }

    "remove" {
        Write-Host "  [..] Removing service: $ServiceName" -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        & $NssmPath remove $ServiceName confirm
        Write-Host "  [OK]  Service removed." -ForegroundColor Green
    }

    "restart" {
        Write-Host "  [..] Restarting service: $ServiceName" -ForegroundColor Yellow
        Restart-Service -Name $ServiceName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc) {
            Write-Host "  Service status: $($svc.Status)" -ForegroundColor $(if ($svc.Status -eq "Running") {"Green"} else {"Yellow"})
        }
    }

    "status" {
        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc) {
            Write-Host "  Service: $($svc.DisplayName)" -ForegroundColor Cyan
            Write-Host "  Status : $($svc.Status)"     -ForegroundColor $(if ($svc.Status -eq "Running") {"Green"} else {"Red"})
            Write-Host "  Start  : $($svc.StartType)"  -ForegroundColor DarkGray

            # Also ping the Hub health endpoint
            try {
                $r = Invoke-WebRequest -Uri "http://localhost:8765/api/health" -TimeoutSec 2 -ErrorAction Stop
                $h = $r.Content | ConvertFrom-Json
                Write-Host "  Hub    : Online -- uptime $($h.uptime_seconds)s  v$($h.version)" -ForegroundColor Green
            } catch {
                Write-Host "  Hub    : Not responding on port 8765" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  Service '$ServiceName' is not installed." -ForegroundColor Red
            Write-Host "  Run: .\hub_install_service.ps1 -Action install" -ForegroundColor Yellow
        }
    }

    default {
        Write-Host "  Unknown action: $Action" -ForegroundColor Red
        Write-Host "  Valid: install | remove | restart | status" -ForegroundColor Yellow
    }
}
Write-Host ""
