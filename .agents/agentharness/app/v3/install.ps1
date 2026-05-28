# ============================================================
#  AgentHarness v3 — Full Install Script (Windows PowerShell)
#
#  BLOCKED BY EXECUTION POLICY? Run this from CMD instead:
#    powershell.exe -ExecutionPolicy Bypass -File ".agents\agentharness\app\v3\install.ps1"
#
#  Or unlock for your user account (one-time, no admin needed):
#    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#
#  What this does:
#    [1]  Verifies Python 3.10+ is installed and on PATH
#    [2]  Checks tkinter is available (required for the GUI)
#    [3]  Creates .venv virtual environment at repo root
#    [4]  Upgrades pip, wheel, setuptools inside .venv
#    [5]  Installs all required Python packages (one by one with status)
#    [6]  Verifies every critical import works inside .venv
#    [7]  Creates / updates .agents\.env with API key prompts
#    [8]  Creates .agents\data\ directory structure + empty JSON files
#    [9]  Writes launch_v3.ps1 (repo root) and start.ps1 (app dir)
#   [10]  Prints final health report
# ============================================================

# NOTE: ErrorActionPreference left at default (Continue) intentionally.
# Setting it to Stop causes pip stderr warnings to kill the script.
$ErrorActionPreference = "Continue"

# ── Resolve paths ────────────────────────────────────────────────────────────
$ScriptDir  = $PSScriptRoot
$RepoRoot   = (Resolve-Path (Join-Path $ScriptDir "../../../../")).Path.TrimEnd('\')
$VenvDir    = Join-Path $RepoRoot ".venv"
$VenvPython = Join-Path $VenvDir  "Scripts\python.exe"
$VenvPip    = Join-Path $VenvDir  "Scripts\pip.exe"
$EnvFile    = Join-Path $RepoRoot ".agents\.env"
$DataDir    = Join-Path $RepoRoot ".agents\data"
$AppScript  = Join-Path $ScriptDir "main_m365.py"

Set-Location $RepoRoot

# ── Helper functions ─────────────────────────────────────────────────────────
function Step-Header($n, $msg) {
    Write-Host ""
    Write-Host "  [$n/10] $msg" -ForegroundColor Cyan
    Write-Host "  $('-' * 54)" -ForegroundColor DarkGray
}
function OK($msg)   { Write-Host "    [OK]   $msg" -ForegroundColor Green }
function WARN($msg) { Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function FAIL($msg) { Write-Host "    [FAIL] $msg" -ForegroundColor Red }
function INFO($msg) { Write-Host "           $msg" -ForegroundColor DarkGray }

# ── Banner ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  +----------------------------------------------------------+" -ForegroundColor Cyan
Write-Host "  |   AgentHarness v3  --  Full Installer (Windows)         |" -ForegroundColor Cyan
Write-Host "  |   Smith Capital Portfolio Agent System                   |" -ForegroundColor Cyan
Write-Host "  +----------------------------------------------------------+" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Repo root : $RepoRoot" -ForegroundColor DarkGray
Write-Host "  App script: $AppScript" -ForegroundColor DarkGray
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Python version check
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 1 "Checking Python installation"

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $verOutput = & $cmd --version 2>&1
        if ($verOutput -match "Python (\d+)\.(\d+)\.?(\d*)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $pythonCmd = $cmd
                OK "Found Python $major.$minor (command: '$cmd')"
                break
            } else {
                WARN "Found Python $major.$minor — need 3.10+. Trying next..."
            }
        }
    } catch {
        # Command not found — try next
    }
}

if (-not $pythonCmd) {
    FAIL "Python 3.10+ not found on PATH."
    INFO "Download from: https://python.org/downloads"
    INFO "During install check: 'Add Python to PATH'"
    INFO ""
    INFO "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — tkinter check
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 2 "Checking tkinter (GUI framework)"

$tkResult = & $pythonCmd -c "import tkinter; print(tkinter.TkVersion)" 2>&1
if ($LASTEXITCODE -eq 0 -and $tkResult -notmatch "Error") {
    OK "tkinter $tkResult is available"
} else {
    FAIL "tkinter not found."
    INFO ""
    INFO "On Windows tkinter is bundled with the official Python installer."
    INFO "Fix: Uninstall Python, re-download from https://python.org"
    INFO "     During install, click 'Modify' and check 'tcl/tk and IDLE'"
    INFO ""
    WARN "Continuing without tkinter — GUI will NOT launch until fixed."
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Create virtual environment
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 3 "Setting up virtual environment"

if (Test-Path $VenvPython) {
    OK "Existing .venv found — skipping creation"
} else {
    INFO "Creating .venv at $VenvDir ..."
    & $pythonCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPython)) {
        FAIL "Failed to create virtual environment."
        INFO "Try running: python -m venv .venv"
        exit 1
    }
    OK "Virtual environment created at .venv"
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Upgrade pip / wheel / setuptools
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 4 "Upgrading pip, wheel, setuptools"

& $VenvPython -m pip install --upgrade pip wheel setuptools --quiet 2>&1 | Out-Null
OK "pip, wheel, setuptools upgraded"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Install packages
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 5 "Installing Python packages"

# Each entry is a separate string — no semicolons, no platform conditionals.
# better-sqlite3 is a Node.js package and does NOT belong here (removed).
$packages = @(
    "langgraph>=0.2.0"
    "langchain>=0.3.0"
    "langchain-core>=0.3.0"
    "langchain-openai>=0.1.0"
    "langchain-community>=0.3.0"
    "openai>=1.0.0"
    "pydantic>=2.0.0"
    "sqlite-utils>=3.35.0"
    "requests>=2.31.0"
    "python-dotenv>=1.0.0"
    "python-dateutil>=2.8.0"
    "markdown>=3.5"
)

Write-Host ""
$failedPkgs = @()

foreach ($pkg in $packages) {
    # Display name: strip version specifier
    $displayName = ($pkg -split ">=")[0].Trim()
    Write-Host "    Installing $($displayName.PadRight(30))" -NoNewline -ForegroundColor DarkGray

    # Run pip quietly, capture stderr separately
    $pipOut = & $VenvPip install $pkg --quiet 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        $failedPkgs += $displayName
        # Print the actual error so user knows why
        if ($pipOut) {
            foreach ($line in $pipOut) {
                INFO "    $line"
            }
        }
    }
}

Write-Host ""
if ($failedPkgs.Count -gt 0) {
    WARN "Failed packages: $($failedPkgs -join ', ')"
    INFO "Re-run install.ps1 after fixing the issue, or install manually:"
    INFO "  .venv\Scripts\pip.exe install <package>"
} else {
    OK "All $($packages.Count) packages installed successfully"
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Verify imports
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 6 "Verifying critical imports"

# Write the verify script to a temp file — avoids pipe encoding issues on PS5
$verifyScriptPath = Join-Path $env:TEMP "ah_verify_$([System.IO.Path]::GetRandomFileName()).py"

@"
import sys

checks = [
    ("tkinter",              "GUI framework (required)"),
    ("tkinter.ttk",          "TTK widgets"),
    ("tkinter.font",         "Tk font module"),
    ("tkinter.scrolledtext", "ScrolledText widget"),
    ("langgraph",            "Agent graph engine"),
    ("langchain",            "LLM chain framework"),
    ("langchain_openai",     "OpenAI connector"),
    ("openai",               "OpenAI SDK"),
    ("pydantic",             "Data validation"),
    ("requests",             "HTTP client"),
    ("dotenv",               "Env file loader"),
    ("sqlite3",              "SQLite DB (stdlib)"),
    ("sqlite_utils",         "SQLite utilities"),
    ("threading",            "Threading (stdlib)"),
    ("json",                 "JSON (stdlib)"),
    ("pathlib",              "Path utilities (stdlib)"),
    ("uuid",                 "UUID (stdlib)"),
    ("datetime",             "Datetime (stdlib)"),
    ("re",                   "Regex (stdlib)"),
    ("ast",                  "AST parser (stdlib)"),
    ("urllib.request",       "HTTP urllib (stdlib)"),
]

ok_count = 0
fail_count = 0
for mod, label in checks:
    try:
        __import__(mod)
        print(f"    OK   {mod:<30} {label}")
        ok_count += 1
    except ImportError as e:
        print(f"    FAIL {mod:<30} {label}")
        print(f"         Error: {e}")
        fail_count += 1

print()
print(f"    Result: {ok_count}/{len(checks)} imports OK  |  {fail_count} failed")
sys.exit(fail_count)
"@ | Set-Content $verifyScriptPath -Encoding UTF8

Write-Host ""
& $VenvPython $verifyScriptPath
$verifyExit = $LASTEXITCODE

Remove-Item $verifyScriptPath -Force -ErrorAction SilentlyContinue

Write-Host ""
if ($verifyExit -eq 0) {
    OK "All imports verified"
} else {
    WARN "$verifyExit import(s) failed — review the list above"
    INFO "The app may still run if failed imports are non-critical"
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Create / update .agents\.env
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 7 "Environment configuration (.agents\.env)"

$envDir = Split-Path $EnvFile -Parent
if (-not (Test-Path $envDir)) {
    New-Item -ItemType Directory -Path $envDir -Force | Out-Null
}

# Read existing .env into hashtable
$existingEnv = @{}
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([A-Za-z_][A-Za-z0-9_]*)=(.*)$") {
            $existingEnv[$Matches[1]] = $Matches[2]
        }
    }
    OK "Existing .env loaded ($($existingEnv.Count) keys)"
} else {
    INFO "No .env found — creating one"
    "# AgentHarness v3 Environment Variables" | Set-Content $EnvFile -Encoding UTF8
}

# Keys to prompt for — using ordered list to guarantee sequence
$keyDefs = [ordered]@{
    "OPENAI_API_KEY"    = "OpenAI API key (sk-proj-...) — powers AgentMajesty LLM chat"
    "GITHUB_PAT"        = "GitHub Personal Access Token — for git push/pull"
    "ANTHROPIC_API_KEY" = "Anthropic API key — optional, for Claude provider"
}

$newKeys = [ordered]@{}
foreach ($key in $keyDefs.Keys) {
    $desc = $keyDefs[$key]
    $isOptional = ($key -eq "ANTHROPIC_API_KEY")

    if ($existingEnv.ContainsKey($key) -and $existingEnv[$key].Trim() -ne "") {
        OK "$key already set"
    } else {
        Write-Host ""
        if ($isOptional) {
            INFO "Optional: $key"
        } else {
            WARN "Missing: $key"
        }
        INFO "  $desc"
        $val = Read-Host "  Enter $key (press Enter to skip)"
        if ($val.Trim() -ne "") {
            $newKeys[$key] = $val.Trim()
            OK "$key will be saved"
        } else {
            if ($isOptional) {
                INFO "Skipped (optional)"
            } else {
                WARN "Skipped — add $key to .agents\.env manually before launching"
            }
        }
    }
}

# Append new keys to .env
if ($newKeys.Count -gt 0) {
    foreach ($key in $newKeys.Keys) {
        # Remove existing line for this key if present, then append
        $envLines = Get-Content $EnvFile
        $envLines = $envLines | Where-Object { $_ -notmatch "^$key=" }
        $envLines += "$key=$($newKeys[$key])"
        $envLines | Set-Content $EnvFile -Encoding UTF8
    }
    OK "$($newKeys.Count) key(s) written to .agents\.env"
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Create data directories and seed files
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 8 "Creating data directories"

$dirsToCreate = @(
    $DataDir
    (Join-Path $DataDir "logs")
    (Join-Path $DataDir "exports")
)

foreach ($dir in $dirsToCreate) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        OK "Created: $(($dir).Replace($RepoRoot, '.'))"
    } else {
        INFO "Exists : $(($dir).Replace($RepoRoot, '.'))"
    }
}

# Seed empty JSON files so the app doesn't crash on first load
$seedFiles = @{
    (Join-Path $DataDir "todos.json")          = "[]"
    (Join-Path $DataDir "scheduled_runs.json") = "[]"
    (Join-Path $DataDir "notifications.json")  = "[]"
}

foreach ($path in $seedFiles.Keys) {
    if (-not (Test-Path $path)) {
        $seedFiles[$path] | Set-Content $path -Encoding UTF8
        OK "Created: $(Split-Path $path -Leaf)"
    } else {
        INFO "Exists : $(Split-Path $path -Leaf)"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — Write launch scripts
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 9 "Writing launch scripts"

# ── start.ps1 (app directory — detailed launcher) ────────────────────────────
$startPs1Path = Join-Path $ScriptDir "start.ps1"
$startPs1Content = @"
# AgentHarness v3 -- Launch Script
# Generated by install.ps1. Run with:
#   powershell.exe -ExecutionPolicy Bypass -File ".agents\agentharness\app\v3\start.ps1"

`$ErrorActionPreference = "Continue"
`$ScriptDir  = `$PSScriptRoot
`$RepoRoot   = (Resolve-Path (Join-Path `$ScriptDir "../../../../")).Path.TrimEnd('\')
`$VenvPython = Join-Path `$RepoRoot ".venv\Scripts\python.exe"
`$AppScript  = Join-Path `$ScriptDir "main_m365.py"
`$EnvFile    = Join-Path `$RepoRoot ".agents\.env"

Set-Location `$RepoRoot

Write-Host ""
Write-Host "  AgentHarness v3 -- Starting..." -ForegroundColor Cyan

if (-not (Test-Path `$VenvPython)) {
    Write-Host "  [FAIL] .venv not found. Run install.ps1 first." -ForegroundColor Red
    pause
    exit 1
}

if (Test-Path `$EnvFile) {
    Get-Content `$EnvFile | ForEach-Object {
        if (`$_ -match "^([A-Za-z_][A-Za-z0-9_]*)=(.+)`$") {
            `$k = `$Matches[1]
            `$v = `$Matches[2].Trim("'").Trim('"')
            [System.Environment]::SetEnvironmentVariable(`$k, `$v, "Process")
        }
    }
    Write-Host "  [OK]   .env loaded" -ForegroundColor Green
}

Write-Host "  [OK]   Launching AgentHarness v3..." -ForegroundColor Green
Write-Host ""
& `$VenvPython `$AppScript
"@

$startPs1Content | Set-Content $startPs1Path -Encoding UTF8
OK "Written: .agents\agentharness\app\v3\start.ps1"

# ── launch_v3.ps1 (repo root — one-click launcher) ───────────────────────────
$launchPs1Path = Join-Path $RepoRoot "launch_v3.ps1"
$launchPs1Content = @"
# AgentHarness v3 -- Root Launcher
# Generated by install.ps1
# Run: powershell.exe -ExecutionPolicy Bypass -File "launch_v3.ps1"

`$target = Join-Path `$PSScriptRoot ".agents\agentharness\app\v3\start.ps1"
if (Test-Path `$target) {
    & `$target
} else {
    Write-Host "[FAIL] start.ps1 not found. Re-run install.ps1." -ForegroundColor Red
    pause
}
"@

$launchPs1Content | Set-Content $launchPs1Path -Encoding UTF8
OK "Written: launch_v3.ps1 (repo root)"

# ── Manual launch instructions ────────────────────────────────────────────────
Write-Host ""
INFO "To launch without any script policy issues, run from CMD:"
INFO "  .venv\Scripts\python.exe .agents\agentharness\app\v3\main_m365.py"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 10 — Final health report
# ─────────────────────────────────────────────────────────────────────────────
Step-Header 10 "Final health report"

$appExists      = Test-Path $AppScript
$venvExists     = Test-Path $VenvPython
$envExists      = Test-Path $EnvFile
$todosExists    = Test-Path (Join-Path $DataDir "todos.json")
$launchExists   = Test-Path $launchPs1Path
$importsOK      = ($verifyExit -eq 0)

$reportItems = @(
    [pscustomobject]@{ Label = "Python found on PATH";           OK = ($null -ne $pythonCmd) }
    [pscustomobject]@{ Label = "Virtual environment (.venv)";    OK = $venvExists             }
    [pscustomobject]@{ Label = "App script (main_m365.py)";      OK = $appExists              }
    [pscustomobject]@{ Label = "Packages installed";             OK = ($failedPkgs.Count -eq 0) }
    [pscustomobject]@{ Label = "All imports verified";           OK = $importsOK              }
    [pscustomobject]@{ Label = ".agents\.env file";              OK = $envExists              }
    [pscustomobject]@{ Label = ".agents\data\todos.json";        OK = $todosExists            }
    [pscustomobject]@{ Label = "launch_v3.ps1 written";         OK = $launchExists           }
)

Write-Host ""
Write-Host "  +----------------------------------------------------------+" -ForegroundColor Cyan
Write-Host "  |   AgentHarness v3  --  Install Report                   |" -ForegroundColor Cyan
Write-Host "  +----------------------------------------------------------+" -ForegroundColor Cyan
Write-Host ""

$allOK = $true
foreach ($item in $reportItems) {
    if ($item.OK) {
        Write-Host "    [OK]   $($item.Label)" -ForegroundColor Green
    } else {
        Write-Host "    [FAIL] $($item.Label)" -ForegroundColor Red
        $allOK = $false
    }
}

Write-Host ""
if ($allOK) {
    Write-Host "  SUCCESS: Installation complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  To launch AgentHarness v3:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "    Option A -- From CMD (no policy needed):" -ForegroundColor White
    Write-Host "      .venv\Scripts\python.exe .agents\agentharness\app\v3\main_m365.py" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    Option B -- PowerShell with bypass:" -ForegroundColor White
    Write-Host "      powershell.exe -ExecutionPolicy Bypass -File launch_v3.ps1" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    Option C -- If you ran Set-ExecutionPolicy RemoteSigned earlier:" -ForegroundColor White
    Write-Host "      .\launch_v3.ps1" -ForegroundColor DarkGray
} else {
    Write-Host "  INCOMPLETE: Review the [FAIL] items above and re-run." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  You can still try the manual launch from CMD:" -ForegroundColor Gray
    Write-Host "    .venv\Scripts\python.exe .agents\agentharness\app\v3\main_m365.py" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  Press any key to exit the installer..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
