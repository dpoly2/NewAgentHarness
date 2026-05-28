# AgentHarness v3 -- Windows Startup Script
# Run from repo root: .\\.agents\\agentharness\\app\\v3\\start.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "../../../../")
Set-Location $repoRoot

Write-Host "`n[H]  AgentHarness v3 -- Starting..." -ForegroundColor Cyan

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[X] Python not found. Install from https://python.org" -ForegroundColor Red
    exit 1
}

# Create/activate venv
$venv = Join-Path $repoRoot ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "[pkg] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venv
}
$activate = Join-Path $venv "Scripts\Activate.ps1"
& $activate

# Install dependencies
Write-Host "[pkg] Installing dependencies..." -ForegroundColor Yellow
pip install --quiet --upgrade langgraph langchain-openai langchain-core

# Set OPENAI_API_KEY from .env if present
$envFile = Join-Path $repoRoot ".agents\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^OPENAI_API_KEY=(.+)$") {
            $env:OPENAI_API_KEY = $Matches[1].Trim()
            Write-Host "[OK] API key loaded from .env" -ForegroundColor Green
        }
    }
}

# Launch the app
Write-Host "`n[>>] Launching AgentHarness v3..." -ForegroundColor Green
python (Join-Path $PSScriptRoot "main.py")
