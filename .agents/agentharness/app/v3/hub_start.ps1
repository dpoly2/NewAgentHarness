# ============================================================
#  AgentHarness Hub — Server Start Script (Windows)
#  Starts the Hub server as a background process.
#
#  Run from CMD (no policy issues):
#    powershell.exe -ExecutionPolicy Bypass -File ".agents\agentharness\app\v3\hub_start.ps1"
#
#  Or from PowerShell (after Set-ExecutionPolicy RemoteSigned):
#    .\.agents\agentharness\app\v3\hub_start.ps1
# ============================================================

$ErrorActionPreference = "Continue"

$ScriptDir  = $PSScriptRoot
$RepoRoot   = (Resolve-Path (Join-Path $ScriptDir "../../../../")).Path.TrimEnd('\')
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$HubScript  = Join-Path $ScriptDir "hub_server.py"
$EnvFile    = Join-Path $RepoRoot ".agents\.env"
$PidFile    = Join-Path $RepoRoot ".agents\data\hub.pid"
$LogFile    = Join-Path $RepoRoot ".agents\data\logs\hub_$(Get-Date -Format 'yyyy-MM-dd').log"

Set-Location $RepoRoot

Write-Host ""
Write-Host "  [Hub] AgentHarness Hub — Starting..." -ForegroundColor Cyan

# ── Check venv ────────────────────────────────────────────────────────────────
if (-not (Test-Path $VenvPython)) {
    Write-Host "  [FAIL] .venv not found. Run install.ps1 first." -ForegroundColor Red
    exit 1
}

# ── Check if Hub already running ──────────────────────────────────────────────
if (Test-Path $PidFile) {
    $existingPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($existingPid) {
        $proc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  [OK]  Hub already running (PID $existingPid)" -ForegroundColor Green
            Write-Host "        REST: http://localhost:8765/api" -ForegroundColor DarkGray
            Write-Host "        WS:   ws://localhost:8765/ws" -ForegroundColor DarkGray
            exit 0
        }
    }
    Remove-Item $PidFile -Force
}

# ── Load .env into environment ────────────────────────────────────────────────
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([A-Za-z_][A-Za-z0-9_]*)=(.+)$") {
            $k = $Matches[1].Trim()
            $v = $Matches[2].Trim().Trim("'").Trim('"')
            [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
        }
    }
    Write-Host "  [OK]  .env loaded" -ForegroundColor Green
}

# ── Start Hub as background process ──────────────────────────────────────────
Write-Host "  [..] Starting Hub server (logging to $LogFile)..." -ForegroundColor Yellow

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName               = $VenvPython
$psi.Arguments              = "`"$HubScript`""
$psi.WorkingDirectory       = $ScriptDir
$psi.UseShellExecute        = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError  = $true
$psi.CreateNoWindow         = $true

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi

# Pipe output to log file
$logDir = Split-Path $LogFile -Parent
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

$proc.Start() | Out-Null

# Wait up to 5s for Hub to become healthy
$ready = $false
$attempts = 0
while ($attempts -lt 10) {
    Start-Sleep -Milliseconds 500
    $attempts++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8765/api/health" -TimeoutSec 1 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        # Not ready yet
    }
}

if ($ready) {
    Write-Host "  [OK]  Hub is online (PID $($proc.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "        REST API : http://localhost:8765/api" -ForegroundColor Cyan
    Write-Host "        WebSocket: ws://localhost:8765/ws" -ForegroundColor Cyan
    Write-Host "        API Docs : http://localhost:8765/docs" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "  [WARN] Hub did not respond within 5s." -ForegroundColor Yellow
    Write-Host "         Check log: $LogFile" -ForegroundColor DarkGray
    Write-Host "         Or run manually: $VenvPython $HubScript" -ForegroundColor DarkGray
}
