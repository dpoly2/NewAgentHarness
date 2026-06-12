# ============================================================
#  ArchonHub — Production Installer
#  Sets up Python venv, installs all dependencies, registers
#  the Hub as a Windows Service, and creates desktop shortcuts.
#
#  Run from repo root (as Administrator recommended):
#    powershell.exe -ExecutionPolicy Bypass -File install.ps1
#
#  Options:
#    -ServiceOnly   Skip venv/pip, only install the Windows service
#    -NoService     Skip Windows service installation
#    -NoShortcuts   Skip desktop shortcut creation
#    -Force         Re-install even if already installed
# ============================================================

param(
    [switch]$ServiceOnly,
    [switch]$NoService,
    [switch]$NoShortcuts,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"   # suppress slow Invoke-WebRequest progress bars

# ── Paths ────────────────────────────────────────────────────
$RepoRoot    = $PSScriptRoot
$AgentsDir   = Join-Path $RepoRoot ".agents"
$AppDir      = Join-Path $AgentsDir "agentharness\app\v3"
$VenvDir     = Join-Path $RepoRoot ".venv"
$VenvPython  = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip     = Join-Path $VenvDir "Scripts\pip.exe"
$Requirements= Join-Path $AppDir "requirements.txt"
$EnvFile     = Join-Path $AgentsDir ".env"
$EnvExample  = Join-Path $AgentsDir ".env.example"
$ServicePs1  = Join-Path $AppDir "hub_install_service.ps1"
$HubScript   = Join-Path $AppDir "hub_server.py"
$DesktopApp  = Join-Path $AppDir "main_m365.py"
$LogDir      = Join-Path $AgentsDir "data\logs"

# ── Console helpers ──────────────────────────────────────────
function Write-Step   { param($n,$t) Write-Host "  [$n] $t" -ForegroundColor Cyan   }
function Write-Ok     { param($t)    Write-Host "  [OK]  $t" -ForegroundColor Green  }
function Write-Warn   { param($t)    Write-Host "  [WARN] $t" -ForegroundColor Yellow }
function Write-Fail   { param($t)    Write-Host "  [FAIL] $t" -ForegroundColor Red    ; exit 1 }
function Write-Info   { param($t)    Write-Host "        $t"  -ForegroundColor DarkGray }

# ── Banner ───────────────────────────────────────────────────
Clear-Host
Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║          ArchonHub — Production Installer             ║" -ForegroundColor Cyan
Write-Host "  ║          AI Agent Orchestration Platform              ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Repo  : $RepoRoot" -ForegroundColor DarkGray
Write-Host "  Venv  : $VenvDir"  -ForegroundColor DarkGray
Write-Host ""

# ── Admin check ──────────────────────────────────────────────
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin -and -not $NoService) {
    Write-Warn "Not running as Administrator."
    Write-Info "Windows Service installation will be skipped."
    Write-Info "Re-run as Administrator to install the service, or use -NoService to suppress this warning."
    $NoService = $true
}

# ════════════════════════════════════════════════════════════
# STEP 1 — Python version check
# ════════════════════════════════════════════════════════════
if (-not $ServiceOnly) {
    Write-Step "1/6" "Checking Python installation..."

    $pythonExe = $null
    foreach ($candidate in @("python", "python3", "py")) {
        try {
            $ver = & $candidate --version 2>&1
            if ($ver -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                if ($major -ge 3 -and $minor -ge 11) {
                    $pythonExe = (Get-Command $candidate -ErrorAction SilentlyContinue).Source
                    if (-not $pythonExe) { $pythonExe = $candidate }
                    Write-Ok "Python $major.$minor found: $pythonExe"
                    break
                } else {
                    Write-Warn "Python $major.$minor is too old (need 3.11+)"
                }
            }
        } catch {}
    }

    if (-not $pythonExe) {
        Write-Fail @"
Python 3.11+ not found.
Download from https://www.python.org/downloads/
Make sure 'Add Python to PATH' is checked during installation.
"@
    }

    # ════════════════════════════════════════════════════════════
    # STEP 2 — Virtual environment
    # ════════════════════════════════════════════════════════════
    Write-Step "2/6" "Setting up Python virtual environment..."

    if ((Test-Path $VenvPython) -and -not $Force) {
        Write-Ok "Virtual environment already exists at $VenvDir"
    } else {
        if (Test-Path $VenvDir) {
            Write-Info "Removing existing venv..."
            Remove-Item $VenvDir -Recurse -Force
        }
        Write-Info "Creating venv..."
        & $pythonExe -m venv $VenvDir
        if (-not (Test-Path $VenvPython)) {
            Write-Fail "Failed to create virtual environment at $VenvDir"
        }
        Write-Ok "Virtual environment created"
    }

    # ════════════════════════════════════════════════════════════
    # STEP 3 — Install Python dependencies
    # ════════════════════════════════════════════════════════════
    Write-Step "3/6" "Installing Python dependencies..."

    if (-not (Test-Path $Requirements)) {
        Write-Fail "requirements.txt not found: $Requirements"
    }

    Write-Info "Upgrading pip..."
    & $VenvPython -m pip install --upgrade pip --quiet

    Write-Info "Installing packages from requirements.txt (this may take a minute)..."
    & $VenvPip install -r $Requirements --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "pip install failed. Check your internet connection and try again."
    }
    Write-Ok "All Python dependencies installed"

    # ════════════════════════════════════════════════════════════
    # STEP 4 — Environment configuration
    # ════════════════════════════════════════════════════════════
    Write-Step "4/6" "Environment configuration..."

    if (Test-Path $EnvFile) {
        Write-Ok ".env already exists at $EnvFile"
        # Warn if JWT_SECRET is still the example placeholder
        $envContent = Get-Content $EnvFile -Raw
        if ($envContent -match "CHANGE-ME") {
            Write-Warn "JWT_SECRET is still set to the placeholder value."
            Write-Info "Edit .agents\.env and set a strong random JWT_SECRET before production use."
            Write-Info "Generate one: python -c `"import secrets; print(secrets.token_hex(32))`""
        }
        if ($envContent -match "^OPENAI_API_KEY=sk-\.\.\." -or $envContent -match "^OPENAI_API_KEY=$") {
            Write-Warn "OPENAI_API_KEY is not set — agent execution will fail without it."
            Write-Info "Edit .agents\.env and add your OpenAI API key."
        }
    } elseif (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Ok ".env created from template at $EnvFile"
        Write-Warn "ACTION REQUIRED: Edit .agents\.env and fill in your API keys."
        Write-Info "  - OPENAI_API_KEY  (required)"
        Write-Info "  - JWT_SECRET      (change to a long random string)"
        Write-Info "  - ADMIN_PASSWORD  (optional, default: ArchonHub2024!)"
    } else {
        Write-Warn ".env.example not found. Creating minimal .env..."
        @"
OPENAI_API_KEY=sk-...
JWT_SECRET=CHANGE-ME-$(([System.Guid]::NewGuid().ToString('N')))
ADMIN_PASSWORD=ArchonHub2024!
HUB_PORT=8765
"@ | Set-Content $EnvFile
        Write-Warn "Edit .agents\.env and replace OPENAI_API_KEY and JWT_SECRET before running."
    }
}

# ════════════════════════════════════════════════════════════
# STEP 5 — Windows Service
# ════════════════════════════════════════════════════════════
if (-not $NoService) {
    Write-Step "5/6" "Installing ArchonHub as a Windows Service..."

    if (-not (Test-Path $ServicePs1)) {
        Write-Warn "hub_install_service.ps1 not found — skipping service install."
    } else {
        $svc = Get-Service -Name "ArchonHub" -ErrorAction SilentlyContinue
        if ($svc -and -not $Force) {
            Write-Ok "Windows service 'ArchonHub' is already installed (status: $($svc.Status))"
            Write-Info "Use -Force to reinstall, or: .\hub_install_service.ps1 -Action restart"
        } else {
            if ($svc -and $Force) {
                Write-Info "Removing existing service for reinstall..."
                & powershell.exe -ExecutionPolicy Bypass -File $ServicePs1 -Action remove
            }
            & powershell.exe -ExecutionPolicy Bypass -File $ServicePs1 -Action install
        }
    }
} else {
    Write-Step "5/6" "Windows Service installation skipped (-NoService or not Administrator)."
    Write-Info "To install later (run as Administrator):"
    Write-Info "  powershell -ExecutionPolicy Bypass -File hub_install_service.ps1 -Action install"
}

# ════════════════════════════════════════════════════════════
# STEP 6 — Desktop Shortcuts
# ════════════════════════════════════════════════════════════
if (-not $NoShortcuts) {
    Write-Step "6/6" "Creating desktop shortcuts..."

    $Desktop   = [Environment]::GetFolderPath("Desktop")
    $WshShell  = New-Object -ComObject WScript.Shell

    # Shortcut 1: ArchonHub Desktop App
    try {
        $sc1 = $WshShell.CreateShortcut("$Desktop\ArchonHub Desktop.lnk")
        $sc1.TargetPath      = $VenvPython
        $sc1.Arguments       = "`"$DesktopApp`""
        $sc1.WorkingDirectory= $AppDir
        $sc1.Description     = "ArchonHub M365 Desktop Client"
        $sc1.IconLocation    = $VenvPython
        $sc1.Save()
        Write-Ok "Shortcut: ArchonHub Desktop.lnk → Desktop"
    } catch {
        Write-Warn "Could not create desktop app shortcut: $_"
    }

    # Shortcut 2: ArchonHub Web Dashboard (URL shortcut)
    try {
        $sc2 = $WshShell.CreateShortcut("$Desktop\ArchonHub Web.url")
        $sc2.TargetPath = "http://localhost:8765/web"
        $sc2.Save()
        Write-Ok "Shortcut: ArchonHub Web.url → Desktop"
    } catch {
        Write-Warn "Could not create web shortcut: $_"
    }

    # Shortcut 3: ArchonHub Launch (Hub + Desktop)
    try {
        $launchPs1 = Join-Path $RepoRoot "launch_v3.ps1"
        if (Test-Path $launchPs1) {
            $sc3 = $WshShell.CreateShortcut("$Desktop\ArchonHub Launch.lnk")
            $sc3.TargetPath       = "powershell.exe"
            $sc3.Arguments        = "-ExecutionPolicy Bypass -File `"$launchPs1`""
            $sc3.WorkingDirectory = $RepoRoot
            $sc3.Description      = "Launch ArchonHub Hub + Desktop App"
            $sc3.Save()
            Write-Ok "Shortcut: ArchonHub Launch.lnk → Desktop"
        }
    } catch {
        Write-Warn "Could not create launch shortcut: $_"
    }
} else {
    Write-Step "6/6" "Desktop shortcuts skipped (-NoShortcuts)."
}

# ════════════════════════════════════════════════════════════
# DONE — Summary
# ════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "  ═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ArchonHub installation complete!" -ForegroundColor Green
Write-Host "  ═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Surfaces:" -ForegroundColor White
Write-Host "    Web Dashboard  →  http://localhost:8765/web" -ForegroundColor Cyan
Write-Host "    REST API       →  http://localhost:8765/api" -ForegroundColor Cyan
Write-Host "    API Docs       →  http://localhost:8765/docs" -ForegroundColor Cyan
Write-Host "    Desktop App    →  ArchonHub Desktop shortcut on your Desktop" -ForegroundColor Cyan
Write-Host "    iOS / Watch    →  Open ArchonHub.xcodeproj in Xcode (Mac required)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Default login:  admin / ArchonHub2024!" -ForegroundColor DarkGray
Write-Host "  Config:         .agents\.env" -ForegroundColor DarkGray
Write-Host "  Logs:           .agents\data\logs\" -ForegroundColor DarkGray
Write-Host ""

# Final health ping (if service was installed)
if (-not $NoService) {
    Start-Sleep -Seconds 2
    try {
        $h = Invoke-RestMethod "http://localhost:8765/api/health" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  Hub status: ONLINE — v$($h.version)" -ForegroundColor Green
    } catch {
        Write-Host "  Hub status: starting (check http://localhost:8765/web in a moment)" -ForegroundColor Yellow
    }
}
Write-Host ""
