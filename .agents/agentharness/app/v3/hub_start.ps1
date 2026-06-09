# ArchonHub — Start Hub Server (headless)
# Resolves repo root, activates .venv, loads .agents/.env, launches hub_server.py

$ErrorActionPreference = "Stop"

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Get-Item $ScriptDir).Parent.Parent.Parent.Parent.FullName
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$FallbackPython = "python"
$EnvFile = Join-Path $RepoRoot ".agents\.env"

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#][^=]*)=(.*)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
    Write-Host "[ArchonHub] Loaded .env"
}

$PythonExe = if (Test-Path $VenvPython) { $VenvPython } else { $FallbackPython }
$HubScript = Join-Path $ScriptDir "hub_server.py"

Write-Host "[ArchonHub Hub] Starting on port 8765..."
Write-Host "[ArchonHub Hub] Web dashboard: http://localhost:8765/web"
Write-Host "[ArchonHub Hub] API docs:      http://localhost:8765/docs"
& $PythonExe $HubScript
