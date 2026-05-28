# AgentHarness — Windows PowerShell Launcher
# Usage: .\start.ps1 [--verify] [--agent <id>] [--project <name>] [--task "<task>"] [--graph <type>]
#
# Examples:
#   .\start.ps1 --verify
#   .\start.ps1 --agent grants-research-agent --project xftc --task "Find 3 grants for youth track"
#   .\start.ps1 --agent xftc-plugin-dev --project xftc --task "Write leaderboard endpoint" --graph wordpress
#   .\start.ps1 --agent grants-research-agent --project yepc --task "Infrastructure grants" --graph research

param(
    [switch]$verify,
    [string]$agent   = "",
    [string]$project = "",
    [string]$task    = "",
    [string]$graph   = "reflexion",
    [string]$env     = "local"
)

# ── Banner ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AgentHarness — LangGraph Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Check Python ─────────────────────────────────────────────────────────────
$python = $null
foreach ($cmd in @("py", "python", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $python = $cmd
        break
    }
}

if (-not $python) {
    Write-Host "❌ Python not found." -ForegroundColor Red
    Write-Host "   Download Python 3.11 from https://www.python.org/downloads/"
    Write-Host "   IMPORTANT: Check 'Add Python to PATH' during install."
    exit 1
}

Write-Host "  Python: $python ($( & $python --version 2>&1 ))" -ForegroundColor Green

# ── Check/activate venv ───────────────────────────────────────────────────────
$venvPath = Join-Path $PSScriptRoot ".venv"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
    & $python -m venv $venvPath
    Write-Host "  ✅ venv created at $venvPath" -ForegroundColor Green
}

if (Test-Path $venvActivate) {
    Write-Host "  Activating venv..." -ForegroundColor Yellow
    & $venvActivate
    Write-Host "  ✅ venv active" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Could not find venv activate script — running without venv" -ForegroundColor Yellow
}

# ── Install dependencies if needed ───────────────────────────────────────────
$reqFile = Join-Path $PSScriptRoot "requirements.txt"
$markerFile = Join-Path $venvPath ".installed"

if (-not (Test-Path $markerFile)) {
    Write-Host "  Installing dependencies..." -ForegroundColor Yellow
    & $python -m pip install -r $reqFile -q
    if ($LASTEXITCODE -eq 0) {
        New-Item -ItemType File -Path $markerFile -Force | Out-Null
        Write-Host "  ✅ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "  ❌ pip install failed — check requirements.txt" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✅ Dependencies already installed" -ForegroundColor Green
}

# ── Check OPENAI_API_KEY ──────────────────────────────────────────────────────
$envFile = Join-Path $PSScriptRoot ".env"
if (-not $env:OPENAI_API_KEY) {
    if (Test-Path $envFile) {
        Write-Host "  Loading .env file..." -ForegroundColor Yellow
        Get-Content $envFile | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.+)$") {
                [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
            }
        }
        Write-Host "  ✅ .env loaded" -ForegroundColor Green
    } elseif (-not $verify) {
        Write-Host ""
        Write-Host "  ⚠️  OPENAI_API_KEY not set." -ForegroundColor Yellow
        Write-Host "  Option 1 — Set it now in this session:"
        Write-Host '  $env:OPENAI_API_KEY = "sk-..."' -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Option 2 — Create a .env file at:"
        Write-Host "  $envFile" -ForegroundColor Cyan
        Write-Host "  Contents:  OPENAI_API_KEY=sk-..."
        Write-Host ""
    }
}

# ── Build args and run ────────────────────────────────────────────────────────
$runScript = Join-Path $PSScriptRoot "run.py"
$pyArgs = @($runScript)

if ($verify) {
    $pyArgs += "--verify"
} else {
    if ($agent)   { $pyArgs += "--agent";   $pyArgs += $agent }
    if ($project) { $pyArgs += "--project"; $pyArgs += $project }
    if ($task)    { $pyArgs += "--task";    $pyArgs += $task }
    if ($graph)   { $pyArgs += "--graph";   $pyArgs += $graph }
    if ($env)     { $pyArgs += "--env";     $pyArgs += $env }
}

Write-Host ""
& $python @pyArgs
