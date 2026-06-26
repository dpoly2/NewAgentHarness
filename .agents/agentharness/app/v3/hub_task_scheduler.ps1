# ============================================================
#  ArchonHub Hub - Windows Task Scheduler Registration
#  Registers hub_server.py to run at user logon via Task Scheduler.
#  Runs as the current user - no password required.
#  No NSSM or Windows Service needed.
#
#  Advantage over Windows Service: Works with Microsoft Store Python
#  and any per-user Python installation (no SYSTEM account conflict).
#
#  Run as Administrator:
#    powershell.exe -ExecutionPolicy Bypass -File hub_task_scheduler.ps1
#
#  Actions:
#    -Action install   (default) - register task and start it
#    -Action remove    - delete the task
#    -Action restart   - kill any running hub then re-run the task
#    -Action status    - show task and hub health
# ============================================================

param(
    [string]$Action = "install"
)

$ErrorActionPreference = "Continue"

$TaskName    = "ArchonHub Hub Server"
$TaskDesc    = "Starts the ArchonHub FastAPI hub server at user logon"
$ScriptDir   = $PSScriptRoot
$RepoRoot    = (Resolve-Path (Join-Path $ScriptDir "../../../../")).Path.TrimEnd('\')
$VenvPython  = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$HubScript   = Join-Path $ScriptDir "hub_server.py"
$EnvFile     = Join-Path $RepoRoot ".agents\.env"

function Write-Banner {
    Write-Host ""
    Write-Host "  +--------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |   ArchonHub Hub - Task Scheduler Manager         |" -ForegroundColor Cyan
    Write-Host "  +--------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  Action : $Action" -ForegroundColor DarkGray
    Write-Host "  Task   : $TaskName" -ForegroundColor DarkGray
    Write-Host ""
}

function Load-EnvBlock {
    $lines = @()
    if (Test-Path $EnvFile) {
        Get-Content $EnvFile | ForEach-Object {
            $trimmed = $_.Trim()
            if ($trimmed -and -not $trimmed.StartsWith('#')) { $lines += $trimmed }
        }
    }
    return $lines -join "`n"
}

Write-Banner

switch ($Action.ToLower()) {

    "install" {
        if (-not (Test-Path $VenvPython)) {
            Write-Host "  [ERROR] venv Python not found: $VenvPython" -ForegroundColor Red
            Write-Host "          Run install.ps1 first." -ForegroundColor Yellow
            exit 1
        }
        if (-not (Test-Path $HubScript)) {
            Write-Host "  [ERROR] hub_server.py not found: $HubScript" -ForegroundColor Red
            exit 1
        }

        # Build the action - pass env vars inline via cmd wrapper
        $envArgs = ""
        if (Test-Path $EnvFile) {
            Get-Content $EnvFile | ForEach-Object {
                if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
                    $k = $Matches[1].Trim()
                    $v = $Matches[2].Trim()
                    $envArgs += "set `"$k=$v`" && "
                }
            }
        }

        $wrapperCmd = "cmd.exe"
        $wrapperArgs = "/c `"$envArgs`"`"$VenvPython`" `"$HubScript`"`""

        # Build scheduled task
        $trigger  = New-ScheduledTaskTrigger -AtLogOn
        $principal= New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Highest
        $action   = New-ScheduledTaskAction -Execute $wrapperCmd -Argument $wrapperArgs -WorkingDirectory $ScriptDir
        $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) -MultipleInstances IgnoreNew

        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Host "  [..] Updating existing task..." -ForegroundColor Yellow
            Set-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
        } else {
            Register-ScheduledTask -TaskName $TaskName -Description $TaskDesc `
                -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
        }

        Write-Host "  [OK]  Task registered: '$TaskName'" -ForegroundColor Green
        Write-Host "        Will auto-start at every user logon." -ForegroundColor DarkGray

        # Start it now
        Write-Host "  [..] Starting task now..." -ForegroundColor Yellow
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 5

        # Health check
        $port = if ($env:HUB_PORT) { $env:HUB_PORT } else { "8765" }
        try {
            $h = Invoke-RestMethod "http://localhost:$port/api/health" -TimeoutSec 6 -ErrorAction Stop
            Write-Host "  [OK]  Hub is live on port $port" -ForegroundColor Green
        } catch {
            Write-Host "  [..] Hub still starting - check http://localhost:$port/web in a moment" -ForegroundColor Yellow
        }

        Write-Host ""
        Write-Host "  Web Dashboard : http://localhost:$port/web"  -ForegroundColor Cyan
        Write-Host "  API Docs      : http://localhost:$port/docs" -ForegroundColor Cyan
        Write-Host ""
    }

    "remove" {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if (-not $task) {
            Write-Host "  Task '$TaskName' not found." -ForegroundColor Yellow
            exit 0
        }
        Stop-ScheduledTask  -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "  [OK]  Task '$TaskName' removed." -ForegroundColor Green
    }

    "restart" {
        # Kill any running hub process
        Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.MainModule.FileName -like "*\.venv\*"
        } | ForEach-Object {
            Write-Host "  [..] Stopping PID $($_.Id)..." -ForegroundColor Yellow
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
        Start-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        $port = if ($env:HUB_PORT) { $env:HUB_PORT } else { "8765" }
        try {
            $h = Invoke-RestMethod "http://localhost:$port/api/health" -TimeoutSec 6 -ErrorAction Stop
            Write-Host "  [OK]  Hub restarted and live on port $port" -ForegroundColor Green
        } catch {
            Write-Host "  Hub not responding yet on port $port" -ForegroundColor Yellow
        }
    }

    "status" {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            $info  = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
            $color = if ($task.State -eq "Running") { "Green" } else { "Yellow" }
            Write-Host "  Task   : $($task.TaskName)" -ForegroundColor Cyan
            Write-Host "  State  : $($task.State)"    -ForegroundColor $color
            Write-Host "  Last run : $($info.LastRunTime)  result: $($info.LastTaskResult)" -ForegroundColor DarkGray
        } else {
            Write-Host "  Task '$TaskName' is not registered." -ForegroundColor Red
            Write-Host "  Run: .\hub_task_scheduler.ps1 -Action install" -ForegroundColor Yellow
        }
        $port = if ($env:HUB_PORT) { $env:HUB_PORT } else { "8765" }
        try {
            $h = Invoke-RestMethod "http://localhost:$port/api/health" -TimeoutSec 3 -ErrorAction Stop
            Write-Host "  Hub    : Online - v$($h.version)  uptime $($h.uptime_seconds)s" -ForegroundColor Green
            Write-Host "  Runs   : $($h.active_runs) active / $($h.queued_runs) queued" -ForegroundColor DarkGray
        } catch {
            Write-Host "  Hub    : Not responding on port $port" -ForegroundColor Yellow
        }
    }

    default {
        Write-Host "  Unknown action: '$Action'" -ForegroundColor Red
        Write-Host "  Valid actions: install | remove | restart | status" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host ""
