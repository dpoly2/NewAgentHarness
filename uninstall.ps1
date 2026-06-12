# ============================================================
#  ArchonHub — Uninstaller
#  Stops and removes the Windows service and desktop shortcuts.
#  Optionally removes the Python virtual environment.
#
#  Run as Administrator:
#    powershell.exe -ExecutionPolicy Bypass -File uninstall.ps1
#
#  Options:
#    -RemoveVenv      Also delete the .venv directory
#    -Force           Skip confirmation prompts
# ============================================================

param(
    [switch]$RemoveVenv,
    [switch]$Force
)

$ErrorActionPreference = "Continue"

$RepoRoot   = $PSScriptRoot
$AgentsDir  = Join-Path $RepoRoot ".agents"
$AppDir     = Join-Path $AgentsDir "agentharness\app\v3"
$VenvDir    = Join-Path $RepoRoot ".venv"
$ServicePs1 = Join-Path $AppDir "hub_install_service.ps1"
$Desktop    = [Environment]::GetFolderPath("Desktop")

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "  ║          ArchonHub — Uninstaller                      ║" -ForegroundColor Yellow
Write-Host "  ╚═══════════════════════════════════════════════════════╝" -ForegroundColor Yellow
Write-Host ""

# Admin check
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "  [WARN] Not running as Administrator — Windows service removal may fail." -ForegroundColor Yellow
}

if (-not $Force) {
    $confirm = Read-Host "  Remove ArchonHub service and shortcuts? (yes/no)"
    if ($confirm -notmatch "^y") {
        Write-Host "  Cancelled." -ForegroundColor DarkGray
        exit 0
    }
}

# ── Remove Windows Service ───────────────────────────────────
Write-Host "  [..] Removing Windows service..." -ForegroundColor Yellow
$svc = Get-Service -Name "ArchonHub" -ErrorAction SilentlyContinue
if ($svc) {
    if (Test-Path $ServicePs1) {
        & powershell.exe -ExecutionPolicy Bypass -File $ServicePs1 -Action remove
    } else {
        Stop-Service -Name "ArchonHub" -Force -ErrorAction SilentlyContinue
        sc.exe delete "ArchonHub" | Out-Null
        Write-Host "  [OK]  Service removed via sc.exe" -ForegroundColor Green
    }
} else {
    Write-Host "  [--]  Service 'ArchonHub' was not installed." -ForegroundColor DarkGray
}

# ── Remove Desktop Shortcuts ─────────────────────────────────
Write-Host "  [..] Removing desktop shortcuts..." -ForegroundColor Yellow
$shortcuts = @(
    "$Desktop\ArchonHub Desktop.lnk",
    "$Desktop\ArchonHub Web.url",
    "$Desktop\ArchonHub Launch.lnk"
)
foreach ($sc in $shortcuts) {
    if (Test-Path $sc) {
        Remove-Item $sc -Force
        Write-Host "  [OK]  Removed: $(Split-Path $sc -Leaf)" -ForegroundColor Green
    }
}

# ── Remove venv (optional) ───────────────────────────────────
if ($RemoveVenv) {
    if (Test-Path $VenvDir) {
        Write-Host "  [..] Removing virtual environment at $VenvDir..." -ForegroundColor Yellow
        Remove-Item $VenvDir -Recurse -Force
        Write-Host "  [OK]  Virtual environment removed." -ForegroundColor Green
    } else {
        Write-Host "  [--]  No virtual environment found at $VenvDir." -ForegroundColor DarkGray
    }
} else {
    Write-Host "  [--]  Virtual environment kept (use -RemoveVenv to delete)." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  ArchonHub has been uninstalled." -ForegroundColor Green
Write-Host "  Database and .env are preserved at .agents\" -ForegroundColor DarkGray
Write-Host ""
