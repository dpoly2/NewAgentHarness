# ============================================================
#  AgentHarness v3 — Full Install & Setup Script (Windows)
#  Run once from repo root:
#      .\\.agents\\agentharness\\app\\v3\\install.ps1
#
#  What it does:
#    1. Verifies Python 3.10+ is installed
#    2. Checks tkinter is available (bundled with Python on Windows)
#    3. Creates a .venv virtual environment at repo root
#    4. Upgrades pip, wheel, setuptools
#    5. Installs ALL required Python packages
#    6. Verifies every critical import works
#    7. Creates/updates .agents/.env with API key prompts
#    8. Creates .agents/data/ directory structure
#    9. Writes start.ps1 convenience launcher
#   10. Prints final health report
# ============================================================

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "AgentHarness v3 Installer"

# ── Resolve paths ────────────────────────────────────────────
$ScriptDir = $PSScriptRoot
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir "../../../../")
$VenvDir   = Join-Path $RepoRoot ".venv"
$EnvFile   = Join-Path $RepoRoot ".agents\.env"
$DataDir   = Join-Path $RepoRoot ".agents\data"
$LogsDir   = Join-Path $DataDir "logs"
$AppScript = Join-Path $ScriptDir "main_m365.py"

Set-Location $RepoRoot

# ── Helpers ──────────────────────────────────────────────────
function Write-Step($n, $msg) {
    Write-Host "`n[$n/10] $msg" -ForegroundColor Cyan
}
function Write-OK($msg)   { Write-Host "    ✅  $msg" -ForegroundColor Green }
function Write-WARN($msg) { Write-Host "    ⚠️   $msg" -ForegroundColor Yellow }
function Write-FAIL($msg) { Write-Host "    ❌  $msg" -ForegroundColor Red }
function Write-INFO($msg) { Write-Host "        $msg" -ForegroundColor Gray }

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       AgentHarness v3 — Full Installer               ║" -ForegroundColor Cyan
Write-Host "║       Smith Capital Portfolio Agent System            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Repo root : $RepoRoot"
Write-Host "  App script: $AppScript"
Write-Host ""

# ── STEP 1: Python version check ─────────────────────────────
Write-Step 1 "Checking Python installation"

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $pythonCmd = $cmd
                Write-OK "Found $ver (using '$cmd')"
                break
            } else {
                Write-WARN "Found $ver — need 3.10+. Trying next..."
            }
        }
    } catch { }
}

if (-not $pythonCmd) {
    Write-FAIL "Python 3.10+ not found."
    Write-INFO "Install from: https://python.org/downloads"
    Write-INFO "Make sure to check 'Add Python to PATH' during install."
    exit 1
}

# ── STEP 2: Check tkinter ─────────────────────────────────────
Write-Step 2 "Checking tkinter (GUI framework)"

$tkCheck = & $pythonCmd -c "import tkinter; print('ok', tkinter.TkVersion)" 2>&1
if ($tkCheck -match "ok") {
    Write-OK "tkinter $($tkCheck.ToString().Split(' ')[1]) — available"
} else {
    Write-FAIL "tkinter not found."
    Write-INFO "On Windows, tkinter is bundled with the official python.org installer."
    Write-INFO "If using a custom Python build, re-install from python.org and"
    Write-INFO "ensure 'tcl/tk and IDLE' is checked in optional features."
    Write-INFO ""
    Write-INFO "Attempted install of fallback: python-tk"
    try {
        & $pythonCmd -m pip install tk 2>&1 | Out-Null
        $tkCheck2 = & $pythonCmd -c "import tkinter; print('ok')" 2>&1
        if ($tkCheck2 -match "ok") { Write-OK "tkinter installed via pip" }
        else { Write-WARN "Could not install tkinter — GUI may not launch. Continuing..." }
    } catch {
        Write-WARN "pip install tk failed — continuing anyway"
    }
}

# ── STEP 3: Create virtual environment ───────────────────────
Write-Step 3 "Setting up virtual environment"

if (Test-Path (Join-Path $VenvDir "Scripts\python.exe")) {
    Write-OK "Existing venv found at .venv"
} else {
    Write-INFO "Creating .venv..."
    & $pythonCmd -m venv $VenvDir
    Write-OK "Virtual environment created at .venv"
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip    = Join-Path $VenvDir "Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-FAIL "Could not locate .venv\Scripts\python.exe"
    exit 1
}

# ── STEP 4: Upgrade pip / wheel / setuptools ─────────────────
Write-Step 4 "Upgrading pip, wheel, setuptools"

& $VenvPython -m pip install --upgrade pip wheel setuptools --quiet
Write-OK "pip, wheel, setuptools up to date"

# ── STEP 5: Install all required packages ────────────────────
Write-Step 5 "Installing Python packages"

# Full requirements list (combines requirements.txt + new app needs)
$packages = @(
    # AI / agent engine
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "langchain-openai>=0.1.0",
    "langchain-core>=0.3.0",
    "langchain-community>=0.3.0",
    "openai>=1.0.0",
    # Data / validation
    "pydantic>=2.0.0",
    "sqlite-utils>=3.35.0",
    # Utilities
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "python-dateutil>=2.8.0",
    # Markdown rendering (used in history view)
    "markdown>=3.5",
    # Optional: better DB performance
    "better-sqlite3; platform_system=='Windows'"
)

Write-INFO "Installing $($packages.Count) packages..."
Write-INFO ""

$failed = @()
foreach ($pkg in $packages) {
    # Extract display name (before >=)
    $name = ($pkg -split ">=|;")[0].Trim()
    Write-Host "        Installing $name..." -NoNewline -ForegroundColor Gray
    try {
        $result = & $VenvPip install $pkg --quiet 2>&1
        Write-Host " ✅" -ForegroundColor Green
    } catch {
        Write-Host " ❌" -ForegroundColor Red
        $failed += $name
    }
}

if ($failed.Count -gt 0) {
    Write-WARN "Some packages failed to install: $($failed -join ', ')"
    Write-INFO "These may be optional or platform-specific. Continuing..."
} else {
    Write-OK "All packages installed successfully"
}

# ── STEP 6: Verify imports ────────────────────────────────────
Write-Step 6 "Verifying critical imports"

$verifyScript = @"
import sys
results = []
checks = [
    ('tkinter',          'GUI framework'),
    ('langgraph',        'Agent graph engine'),
    ('langchain',        'LLM chain framework'),
    ('langchain_openai', 'OpenAI connector'),
    ('openai',           'OpenAI SDK'),
    ('pydantic',         'Data validation'),
    ('requests',         'HTTP client'),
    ('dotenv',           'Env file loader'),
    ('sqlite3',          'SQLite DB (stdlib)'),
    ('sqlite_utils',     'SQLite utilities'),
    ('threading',        'Threading (stdlib)'),
    ('tkinter.ttk',      'ttk widgets'),
    ('tkinter.font',     'Tk fonts'),
    ('tkinter.scrolledtext', 'ScrolledText'),
    ('json',             'JSON (stdlib)'),
    ('pathlib',          'Pathlib (stdlib)'),
    ('uuid',             'UUID (stdlib)'),
    ('datetime',         'Datetime (stdlib)'),
    ('re',               'Regex (stdlib)'),
    ('ast',              'AST (stdlib)'),
    ('urllib.request',   'URL (stdlib)'),
]
for mod, label in checks:
    try:
        __import__(mod)
        results.append(('OK', mod, label))
    except ImportError as e:
        results.append(('FAIL', mod, f'{label} — {e}'))
for status, mod, label in results:
    icon = '✅' if status == 'OK' else '❌'
    print(f'  {icon}  {mod:<28} {label}')
fails = [r for r in results if r[0]=='FAIL']
print(f'\nResult: {len(results)-len(fails)}/{len(results)} imports OK')
sys.exit(1 if fails else 0)
"@

$verifyScript | & $VenvPython -
$verifyExit = $LASTEXITCODE

if ($verifyExit -eq 0) {
    Write-OK "All critical imports verified"
} else {
    Write-WARN "Some imports failed — see list above"
    Write-INFO "The app may still launch if the failing imports are optional"
}

# ── STEP 7: Create/update .agents/.env ───────────────────────
Write-Step 7 "Environment configuration (.agents/.env)"

$envDir = Split-Path $EnvFile -Parent
if (-not (Test-Path $envDir)) { New-Item -ItemType Directory -Path $envDir -Force | Out-Null }

# Read existing env
$existingEnv = @{}
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#=]+)=(.*)$") {
            $existingEnv[$Matches[1].Trim()] = $Matches[2].Trim()
        }
    }
    Write-OK "Existing .env loaded ($($existingEnv.Count) keys found)"
}

# Prompt for missing keys
$requiredKeys = @{
    "OPENAI_API_KEY"  = "OpenAI API key (sk-...) — required for AgentMajesty LLM chat"
    "GITHUB_PAT"      = "GitHub Personal Access Token — required for code push/pull"
}
$optional = @{
    "ANTHROPIC_API_KEY" = "Anthropic API key — optional, for Claude provider"
}

$newKeys = @{}
foreach ($key in $requiredKeys.Keys) {
    if ($existingEnv.ContainsKey($key) -and $existingEnv[$key] -ne "") {
        Write-OK "$key already set"
    } else {
        Write-WARN "$key not found"
        Write-INFO "  $($requiredKeys[$key])"
        $val = Read-Host "  Enter $key (leave blank to skip)"
        if ($val.Trim() -ne "") { $newKeys[$key] = $val.Trim() }
        else { Write-WARN "  Skipped — you can add it to .agents\.env manually later" }
    }
}
foreach ($key in $optional.Keys) {
    if (-not ($existingEnv.ContainsKey($key) -and $existingEnv[$key] -ne "")) {
        $val = Read-Host "  Enter $key (optional — press Enter to skip)"
        if ($val.Trim() -ne "") { $newKeys[$key] = $val.Trim() }
    } else {
        Write-OK "$key already set (optional)"
    }
}

# Write new/updated env file
if ($newKeys.Count -gt 0) {
    $lines = @()
    if (Test-Path $EnvFile) { $lines = Get-Content $EnvFile }
    foreach ($key in $newKeys.Keys) {
        $escaped = $newKeys[$key]
        # Check if line exists and update it
        $found = $false
        $lines = $lines | ForEach-Object {
            if ($_ -match "^$key=") { $found = $true; "$key=$escaped" }
            else { $_ }
        }
        if (-not $found) { $lines += "$key=$escaped" }
    }
    $lines | Set-Content $EnvFile -Encoding UTF8
    Write-OK "Updated .agents\.env ($($newKeys.Count) keys written)"
} else {
    Write-OK ".env unchanged"
}

# ── STEP 8: Create data directory structure ───────────────────
Write-Step 8 "Creating data directories"

$dirs = @(
    $DataDir,
    $LogsDir,
    (Join-Path $DataDir "scheduled_runs"),
    (Join-Path $DataDir "exports")
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-OK "Created: $($dir.Replace($RepoRoot.ToString(),'.'))"
    } else {
        Write-INFO "Exists : $($dir.Replace($RepoRoot.ToString(),'.'))"
    }
}

# Pre-create empty todos.json if missing
$todosFile = Join-Path $DataDir "todos.json"
if (-not (Test-Path $todosFile)) {
    "[]" | Set-Content $todosFile -Encoding UTF8
    Write-OK "Created: .agents\data\todos.json"
}
$scheduledFile = Join-Path $DataDir "scheduled_runs.json"
if (-not (Test-Path $scheduledFile)) {
    "[]" | Set-Content $scheduledFile -Encoding UTF8
    Write-OK "Created: .agents\data\scheduled_runs.json"
}

# ── STEP 9: Write launch script ──────────────────────────────
Write-Step 9 "Writing launch script (start.ps1)"

$launchScript = @'
# ============================================================
#  AgentHarness v3 — Launch Script (auto-generated by install.ps1)
#  Run from anywhere:  .\\.agents\\agentharness\\app\\v3\\start.ps1
# ============================================================
$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir "../../../../")
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$AppScript  = Join-Path $ScriptDir "main_m365.py"
$EnvFile    = Join-Path $RepoRoot ".agents\.env"

Set-Location $RepoRoot

Write-Host ""
Write-Host "  ⬡  AgentHarness v3 — Starting..." -ForegroundColor Cyan

# Verify venv
if (-not (Test-Path $VenvPython)) {
    Write-Host "  ❌ Virtual environment not found." -ForegroundColor Red
    Write-Host "     Run install.ps1 first." -ForegroundColor Gray
    exit 1
}

# Load .env into environment
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#=\s][^=]*)=(.+)$") {
            $k = $Matches[1].Trim()
            $v = $Matches[2].Trim().Trim("'").Trim('"')
            [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
        }
    }
    Write-Host "  ✅  .env loaded" -ForegroundColor Green
}

Write-Host "  🚀  Launching main_m365.py..." -ForegroundColor Green
Write-Host ""
& $VenvPython $AppScript
'@

$launchScript | Set-Content (Join-Path $ScriptDir "start.ps1") -Encoding UTF8
Write-OK "Written: .agents\agentharness\app\v3\start.ps1"

# Also write a short root-level launcher for convenience
$rootLauncher = @"
# Quick launcher — double-click this from repo root
# Or run: .\launch_v3.ps1
& (Join-Path `$PSScriptRoot ".agents\agentharness\app\v3\start.ps1")
"@
$rootLauncher | Set-Content (Join-Path $RepoRoot "launch_v3.ps1") -Encoding UTF8
Write-OK "Written: launch_v3.ps1  (root-level convenience launcher)"

# ── STEP 10: Final health report ─────────────────────────────
Write-Step 10 "Final health check"

$appExists   = Test-Path $AppScript
$venvExists  = Test-Path $VenvPython
$envExists   = Test-Path $EnvFile
$todosExists = Test-Path $todosFile

Write-Host ""
Write-Host "  ┌─────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "  │            AgentHarness v3 — Install Report          │" -ForegroundColor Cyan
Write-Host "  └─────────────────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""

$checks = @(
    @{ Label="Python $($pythonCmd)";           OK=$true },
    @{ Label="Virtual environment (.venv)";     OK=$venvExists },
    @{ Label="App script (main_m365.py)";       OK=$appExists },
    @{ Label=".agents\.env";                    OK=$envExists },
    @{ Label=".agents\data\todos.json";         OK=$todosExists },
    @{ Label="All imports verified";            OK=($verifyExit -eq 0) }
)

foreach ($c in $checks) {
    $icon  = if ($c.OK) { "✅" } else { "❌" }
    $color = if ($c.OK) { "Green" } else { "Red" }
    Write-Host "  $icon  $($c.Label)" -ForegroundColor $color
}

$allOK = ($checks | Where-Object { -not $_.OK }).Count -eq 0

Write-Host ""
if ($allOK) {
    Write-Host "  ✅  Installation complete — everything looks good!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  ▶  To launch AgentHarness v3, run:" -ForegroundColor Cyan
    Write-Host "       .\launch_v3.ps1" -ForegroundColor White
    Write-Host "     or:" -ForegroundColor Gray
    Write-Host "       .\.agents\agentharness\app\v3\start.ps1" -ForegroundColor White
} else {
    Write-Host "  ⚠️   Installation completed with warnings." -ForegroundColor Yellow
    Write-Host "      Review the ❌ items above and re-run if needed." -ForegroundColor Gray
    Write-Host ""
    Write-Host "  ▶  You can still try launching:" -ForegroundColor Cyan
    Write-Host "       .\launch_v3.ps1" -ForegroundColor White
}
Write-Host ""
