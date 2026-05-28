# AgentHarness v2 — GUI Launcher (Windows PowerShell)
# Run this from anywhere: .\launch.ps1

param([switch]$install)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot   # .agents/agentharness/

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AgentHarness v2 — Desktop App" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Find Python ──────────────────────────────────────────────────────────────
$python = $null
foreach ($cmd in @("py", "python", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $python = $cmd; break
    }
}
if (-not $python) {
    Write-Host "❌ Python not found. Download from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "   Check 'Add Python to PATH' during install."
    exit 1
}
Write-Host "  Python : $( & $python --version 2>&1 )" -ForegroundColor Green

# ── Activate / create venv ────────────────────────────────────────────────────
$venv    = Join-Path $root ".venv"
$activate = Join-Path $venv "Scripts\Activate.ps1"

if (-not (Test-Path $venv)) {
    Write-Host "  Creating venv…" -ForegroundColor Yellow
    & $python -m venv $venv
}
if (Test-Path $activate) { & $activate }

# ── Install deps ──────────────────────────────────────────────────────────────
$marker = Join-Path $venv ".installed"
$req    = Join-Path $root "requirements.txt"

if ($install -or -not (Test-Path $marker)) {
    Write-Host "  Installing dependencies…" -ForegroundColor Yellow
    & $python -m pip install -r $req -q
    New-Item -ItemType File -Path $marker -Force | Out-Null
    Write-Host "  ✅ Dependencies ready" -ForegroundColor Green
}

# ── Load .env ──────────────────────────────────────────────────────────────────
$envFile = Join-Path $root ".env"
if (-not $env:OPENAI_API_KEY -and (Test-Path $envFile)) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.+)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
    Write-Host "  ✅ .env loaded" -ForegroundColor Green
}

if (-not $env:OPENAI_API_KEY) {
    Write-Host ""
    Write-Host "  ⚠  OPENAI_API_KEY not set." -ForegroundColor Yellow
    Write-Host "  Create $envFile with:" -ForegroundColor Yellow
    Write-Host "  OPENAI_API_KEY=sk-..." -ForegroundColor Cyan
    Write-Host ""
}

# ── Launch GUI ────────────────────────────────────────────────────────────────
Write-Host "  Launching AgentHarness v2…" -ForegroundColor Cyan
Write-Host ""
$mainPy = Join-Path $PSScriptRoot "main.py"
& $python $mainPy
