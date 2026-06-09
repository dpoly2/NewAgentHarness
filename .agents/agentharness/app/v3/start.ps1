# ArchonHub — Start Desktop App
# Resolves repo root, activates .venv, loads .agents/.env, launches main_m365.py

$ErrorActionPreference = "Stop"

# Windows Unicode safety
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# Resolve paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Get-Item $ScriptDir).Parent.Parent.Parent.Parent.FullName
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$FallbackPython = "python"
$EnvFile = Join-Path $RepoRoot ".agents\.env"

# Load .env if it exists
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#][^=]*)=(.*)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
    Write-Host "[ArchonHub] Loaded .env from $EnvFile"
}

# Pick Python
$PythonExe = if (Test-Path $VenvPython) { $VenvPython } else { $FallbackPython }
Write-Host "[ArchonHub] Python: $PythonExe"

# Launch desktop app
$MainScript = Join-Path $ScriptDir "main_m365.py"
Write-Host "[ArchonHub] Starting desktop app..."
& $PythonExe $MainScript
