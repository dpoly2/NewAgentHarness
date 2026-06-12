# ============================================================
#  ArchonHub Hub — Windows Service Manager
#  Registers hub_server.py as a Windows Service using NSSM
#  (Non-Sucking Service Manager — free, no pywin32 needed)
#
#  Run as Administrator:
#    powershell.exe -ExecutionPolicy Bypass -File hub_install_service.ps1
#
#  Actions:
#    -Action install   (default) — install and start service
#    -Action remove    — stop and remove service
#    -Action restart   — restart service
#    -Action status    — show current service status
# ============================================================

param(
    [string]$Action = "install"
)

$ErrorActionPreference = "Continue"

$ServiceName = "ArchonHub"
$DisplayName = "ArchonHub Hub Server"
$Description = "Always-on AI agent orchestration server for ArchonHub — Smith Capital Portfolio"

$ScriptDir  = $PSScriptRoot
$RepoRoot   = (Resolve-Path (Join-Path $ScriptDir "../../../../")).Path.TrimEnd('\')
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$HubScript  = Join-Path $ScriptDir "hub_server.py"
$NssmPath   = Join-Path $RepoRoot ".agents\tools\nssm.exe"
$NssmDir    = Split-Path $NssmPath -Parent
$LogDir     = Join-Path $RepoRoot ".agents\data\logs"
$EnvFile    = Join-Path $RepoRoot ".agents\.env"

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║   ArchonHub Hub — Windows Service Manager        ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host "  Action : $Action" -ForegroundColor DarkGray
    Write-Host "  Service: $ServiceName" -ForegroundColor DarkGray
    Write-Host ""
}

function Ensure-Admin {
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
               ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "  [ERROR] Must run as Administrator to manage Windows Services." -ForegroundColor Red
        Write-Host "          Right-click PowerShell → 'Run as Administrator'" -ForegroundColor Yellow
        exit 1
    }
}

function Ensure-Nssm {
    if (Test-Path $NssmPath) { return }
    Write-Host "  [..] Downloading NSSM (Non-Sucking Service Manager)..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $NssmDir -Force | Out-Null
    $NssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $ZipPath = Join-Path $env:TEMP "nssm.zip"
    try {
        Invoke-WebRequest -Uri $NssmUrl -OutFile $ZipPath -ErrorAction Stop
        Expand-Archive -Path $ZipPath -DestinationPath (Join-Path $env:TEMP "nssm_extracted") -Force
        $found = Get-ChildItem -Path (Join-Path $env:TEMP "nssm_extracted") -Recurse -Filter "nssm.exe" |
                 Where-Object { $_.FullName -match "win64" } | Select-Object -First 1
        if (-not $found) {
            $found = Get-ChildItem -Path (Join-Path $env:TEMP "nssm_extracted") -Recurse -Filter "nssm.exe" |
                     Select-Object -First 1
        }
        if ($found) {
            Copy-Item $found.FullName $NssmPath -Force
            Write-Host "  [OK]  NSSM ready at $NssmPath" -ForegroundColor Green
        } else {
            throw "nssm.exe not found in downloaded archive"
        }
    } catch {
        Write-Host "  [FAIL] Could not download NSSM: $_" -ForegroundColor Red
        Write-Host "         Download manually from https://nssm.cc and place nssm.exe at:" -ForegroundColor Yellow
        Write-Host "         $NssmPath" -ForegroundColor DarkGray
        exit 1
    }
}

function Load-EnvVars {
    $vars = @{}
    if (Test-Path $EnvFile) {
        Get-Content $EnvFile | ForEach-Object {
            if ($_ -match "^([A-Za-z_][A-Za-z0-9_]*)=(.+)$") {
                $v = $Matches[2].Trim()
                if ($v -match "^`"(.+)`"`$")  { $v = $Matches[1] }
                elseif ($v -match "^'(.+)'`$") { $v = $Matches[1] }
                $vars[$Matches[1].Trim()] = $v
            }
        }
        Write-Host "  [OK]  Loaded .env from $EnvFile" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] No .env found at $EnvFile — service will use system environment." -ForegroundColor Yellow
        Write-Host "         Copy .agents\.env.example to .agents\.env and set your API keys." -ForegroundColor DarkGray
    }
    return $vars
}

# ──────────────────────────────────────────────────────────────
Write-Banner
Ensure-Admin

switch ($Action.ToLower()) {

    "install" {
        Ensure-Nssm

        # Verify python and script exist
        if (-not (Test-Path $VenvPython)) {
            Write-Host "  [ERROR] venv Python not found: $VenvPython" -ForegroundColor Red
            Write-Host "          Run install.ps1 first to set up the virtual environment." -ForegroundColor Yellow
            exit 1
        }
        if (-not (Test-Path $HubScript)) {
            Write-Host "  [ERROR] hub_server.py not found: $HubScript" -ForegroundColor Red
            exit 1
        }

        $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Host "  [WARN] Service '$ServiceName' is already installed." -ForegroundColor Yellow
            Write-Host "         Use -Action restart or -Action remove first." -ForegroundColor DarkGray
            $existing | Format-List Name, Status, StartType
            exit 0
        }

        Write-Host "  [..] Installing Windows service: $ServiceName" -ForegroundColor Yellow

        $envVars = Load-EnvVars

        # Install and configure via NSSM
        & $NssmPath install $ServiceName $VenvPython $HubScript
        & $NssmPath set $ServiceName AppDirectory $ScriptDir
        & $NssmPath set $ServiceName DisplayName  $DisplayName
        & $NssmPath set $ServiceName Description  $Description
        & $NssmPath set $ServiceName Start        SERVICE_AUTO_START

        # Logs
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
        & $NssmPath set $ServiceName AppStdout        (Join-Path $LogDir "hub-service-stdout.log")
        & $NssmPath set $ServiceName AppStderr        (Join-Path $LogDir "hub-service-stderr.log")
        & $NssmPath set $ServiceName AppRotateFiles   1
        & $NssmPath set $ServiceName AppRotateSeconds 86400

        # Auto-restart on crash after 5 seconds
        & $NssmPath set $ServiceName AppRestartDelay 5000

        # Inject .env variables into service environment
        foreach ($key in $envVars.Keys) {
            & $NssmPath set $ServiceName AppEnvironmentExtra "$key=$($envVars[$key])"
        }

        # Start the service
        Write-Host "  [..] Starting service..." -ForegroundColor Yellow
        Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 4

        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -eq "Running") {
            # Verify HTTP health
            try {
                $h = Invoke-RestMethod "http://localhost:8765/api/health" -TimeoutSec 5 -ErrorAction Stop
                Write-Host "  [OK]  Service installed and hub is live." -ForegroundColor Green
            } catch {
                Write-Host "  [OK]  Service is running (hub may still be starting)." -ForegroundColor Green
            }
            Write-Host ""
            Write-Host "  ┌─────────────────────────────────────────┐" -ForegroundColor Cyan
            Write-Host "  │  Web Dashboard : http://localhost:8765/web  │" -ForegroundColor White
            Write-Host "  │  REST API      : http://localhost:8765/api  │" -ForegroundColor White
            Write-Host "  │  API Docs      : http://localhost:8765/docs │" -ForegroundColor White
            Write-Host "  │  WebSocket     : ws://localhost:8765/ws     │" -ForegroundColor White
            Write-Host "  └─────────────────────────────────────────┘" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  ArchonHub will now start automatically when Windows boots." -ForegroundColor Green
        } else {
            Write-Host "  [WARN] Service installed but status: $($svc.Status)" -ForegroundColor Yellow
            Write-Host "         Check logs: $LogDir\hub-service-stderr.log" -ForegroundColor DarkGray
        }
    }

    "remove" {
        Ensure-Nssm
        Write-Host "  [..] Stopping and removing service: $ServiceName" -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        & $NssmPath remove $ServiceName confirm
        Write-Host "  [OK]  Service '$ServiceName' removed." -ForegroundColor Green
    }

    "restart" {
        Write-Host "  [..] Restarting service: $ServiceName" -ForegroundColor Yellow
        Restart-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc) {
            $color = if ($svc.Status -eq "Running") { "Green" } else { "Yellow" }
            Write-Host "  Service status: $($svc.Status)" -ForegroundColor $color
        }
    }

    "status" {
        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc) {
            $color = if ($svc.Status -eq "Running") { "Green" } else { "Red" }
            Write-Host "  Service : $($svc.DisplayName)" -ForegroundColor Cyan
            Write-Host "  Status  : $($svc.Status)"      -ForegroundColor $color
            Write-Host "  Startup : $($svc.StartType)"   -ForegroundColor DarkGray
            try {
                $h = Invoke-RestMethod "http://localhost:8765/api/health" -TimeoutSec 3 -ErrorAction Stop
                Write-Host "  Hub     : Online — v$($h.version)  uptime $($h.uptime_seconds)s" -ForegroundColor Green
                Write-Host "  Runs    : $($h.active_runs) active / $($h.queued_runs) queued" -ForegroundColor DarkGray
            } catch {
                Write-Host "  Hub     : Not responding on port 8765" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  Service '$ServiceName' is not installed." -ForegroundColor Red
            Write-Host "  Run: .\hub_install_service.ps1 -Action install" -ForegroundColor Yellow
        }
    }

    default {
        Write-Host "  Unknown action: '$Action'" -ForegroundColor Red
        Write-Host "  Valid actions: install | remove | restart | status" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host ""
