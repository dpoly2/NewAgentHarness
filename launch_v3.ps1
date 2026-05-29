# AgentHarness v3 -- Root Launcher
# Run from repo root:
#   powershell.exe -ExecutionPolicy Bypass -File "launch_v3.ps1"
#
# If venv does not exist yet, run install first:
#   powershell.exe -ExecutionPolicy Bypass -File ".agents\agentharness\app\v3\install.ps1"

$target = Join-Path $PSScriptRoot ".agents\agentharness\app\v3\start.ps1"
if (Test-Path $target) {
    & $target
} else {
    Write-Host "[FAIL] start.ps1 not found. Run install.ps1 first." -ForegroundColor Red
    Write-Host "       Expected: $target" -ForegroundColor DarkGray
    pause
}
