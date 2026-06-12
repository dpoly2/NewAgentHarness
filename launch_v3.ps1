# ArchonHub — Full Stack Launch (Hub + Desktop)
# Starts hub_server.py only if not already running, then launches main_m365.py

$ErrorActionPreference = "Continue"

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$RepoRoot    = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir      = Join-Path $RepoRoot ".agents\agentharness\app\v3"
$VenvPython  = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$FallbackPython = "python"
$EnvFile     = Join-Path $RepoRoot ".agents\.env"
$HubScript   = Join-Path $AppDir "hub_server.py"
$DesktopScript = Join-Path $AppDir "main_m365.py"

# Load .env
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#=][^=]*)=(.*)$") {
            [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
}

$PythonExe = if (Test-Path $VenvPython) { $VenvPython } else { $FallbackPython }
$HubPort   = if ($env:HUB_PORT) { $env:HUB_PORT } else { "8765" }

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     ArchonHub v1.0.0 — Full Stack        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Hub Server — only start if not already running ────────────────────────
$hubUp = $false
try {
    Invoke-RestMethod "http://localhost:$HubPort/api/health" -TimeoutSec 2 -ErrorAction Stop | Out-Null
    $hubUp = $true
} catch {}

if ($hubUp) {
    Write-Host "[1/2] Hub Server already running on port $HubPort — skipping." -ForegroundColor Green
} else {
    Write-Host "[1/2] Starting Hub Server on port $HubPort (new window)..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", `
        "cd '$AppDir'; `$env:PYTHONIOENCODING='utf-8'; `$env:PYTHONUTF8='1'; & '$PythonExe' '$HubScript'"

    # Wait up to 20s for hub to be ready
    $ready = $false
    for ($i = 0; $i -lt 10; $i++) {
        Start-Sleep -Seconds 2
        try {
            Invoke-RestMethod "http://localhost:$HubPort/api/health" -TimeoutSec 2 -ErrorAction Stop | Out-Null
            $ready = $true; break
        } catch {}
    }
    if ($ready) {
        Write-Host "       Hub is live on port $HubPort" -ForegroundColor Green
    } else {
        Write-Host "       Hub not responding yet — check the hub window for errors." -ForegroundColor Yellow
    }
}

# ── Desktop App ───────────────────────────────────────────────────────────
Write-Host "[2/2] Starting Desktop App..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Web Dashboard : http://localhost:$HubPort/web"  -ForegroundColor Cyan
Write-Host "  API Docs      : http://localhost:$HubPort/docs" -ForegroundColor Cyan
Write-Host ""
& $PythonExe $DesktopScript

