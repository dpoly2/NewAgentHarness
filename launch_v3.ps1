# ArchonHub — Full Stack Launch (Hub + Desktop)
# Starts hub_server.py in a new background window, then main_m365.py in current window

$ErrorActionPreference = "Stop"

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = Join-Path $RepoRoot ".agents\agentharness\app\v3"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$FallbackPython = "python"
$EnvFile = Join-Path $RepoRoot ".agents\.env"

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#][^=]*)=(.*)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

$PythonExe = if (Test-Path $VenvPython) { $VenvPython } else { $FallbackPython }

Write-Host "╔══════════════════════════════════════════╗"
Write-Host "║     ArchonHub v1.0.0 — Full Stack        ║"
Write-Host "╚══════════════════════════════════════════╝"
Write-Host ""

# Start Hub in a new window
$HubScript = Join-Path $AppDir "hub_server.py"
Write-Host "[1/2] Starting Hub Server (new window)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$AppDir'; $env:PYTHONIOENCODING='utf-8'; & '$PythonExe' '$HubScript'"

# Brief pause
Start-Sleep -Seconds 2

# Start Desktop App in current window
$DesktopScript = Join-Path $AppDir "main_m365.py"
Write-Host "[2/2] Starting Desktop App..."
Write-Host ""
Write-Host "  Web Dashboard: http://localhost:8765/web"
Write-Host "  API Docs:      http://localhost:8765/docs"
Write-Host ""
& $PythonExe $DesktopScript
