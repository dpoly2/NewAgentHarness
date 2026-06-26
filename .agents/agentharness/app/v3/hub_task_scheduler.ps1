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

        # Build an XML task definition - more reliable than PowerShell CIM cmdlets
        # across different Windows versions and execution environments.
        $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        $port = if ($env:HUB_PORT) { $env:HUB_PORT } else { "8765" }

        # Build env-var SET chain for cmd wrapper
        $envChain = ""
        if (Test-Path $EnvFile) {
            Get-Content $EnvFile | ForEach-Object {
                $line = $_.Trim()
                if ($line -and -not $line.StartsWith('#') -and $line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
                    $k = $Matches[1].Trim()
                    $v = $Matches[2].Trim()
                    $envChain += "set `"$k=$v`" &amp;&amp; "
                }
            }
        }
        # cmd /c "set KEY=VAL && ... && python hub_server.py"
        $cmdArgs = "/c `"cd /d `"$ScriptDir`" &amp;&amp; ${envChain}`"$VenvPython`" `"$HubScript`"`""

        $taskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>$TaskDesc</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>$currentUser</UserId>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$currentUser</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <RestartOnFailure>
      <Interval>PT5M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>cmd.exe</Command>
      <Arguments>$cmdArgs</Arguments>
      <WorkingDirectory>$ScriptDir</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

        # Delete old task if present
        $existing = & schtasks.exe /Query /TN $TaskName 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [..] Removing old task..." -ForegroundColor Yellow
            & schtasks.exe /Delete /TN $TaskName /F | Out-Null
        }

        # Register via XML
        $tmpXml = [System.IO.Path]::GetTempFileName() + ".xml"
        [System.IO.File]::WriteAllText($tmpXml, $taskXml, [System.Text.Encoding]::Unicode)
        & schtasks.exe /Create /TN $TaskName /XML $tmpXml /F 2>&1 | Out-Null
        Remove-Item $tmpXml -Force -ErrorAction SilentlyContinue

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [ERROR] schtasks /Create failed (exit $LASTEXITCODE)" -ForegroundColor Red
            exit 1
        }

        Write-Host "  [OK]  Task registered: '$TaskName'" -ForegroundColor Green
        Write-Host "        Will auto-start at every user logon." -ForegroundColor DarkGray

        # Start it now
        Write-Host "  [..] Starting task now..." -ForegroundColor Yellow
        & schtasks.exe /Run /TN $TaskName | Out-Null
        Start-Sleep -Seconds 6

        # Health check
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
        $existing = & schtasks.exe /Query /TN $TaskName 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Task '$TaskName' not found." -ForegroundColor Yellow
            exit 0
        }
        & schtasks.exe /End    /TN $TaskName 2>&1 | Out-Null
        & schtasks.exe /Delete /TN $TaskName /F  2>&1 | Out-Null
        Write-Host "  [OK]  Task '$TaskName' removed." -ForegroundColor Green
    }

    "restart" {
        Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            try { $_.MainModule.FileName -like "*\.venv\*" } catch { $false }
        } | ForEach-Object {
            Write-Host "  [..] Stopping PID $($_.Id)..." -ForegroundColor Yellow
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
        & schtasks.exe /Run /TN $TaskName 2>&1 | Out-Null
        Start-Sleep -Seconds 6
        $port = if ($env:HUB_PORT) { $env:HUB_PORT } else { "8765" }
        try {
            $h = Invoke-RestMethod "http://localhost:$port/api/health" -TimeoutSec 6 -ErrorAction Stop
            Write-Host "  [OK]  Hub restarted and live on port $port" -ForegroundColor Green
        } catch {
            Write-Host "  Hub not responding yet on port $port" -ForegroundColor Yellow
        }
    }

    "status" {
        $query = & schtasks.exe /Query /TN $TaskName /FO LIST 2>&1
        if ($LASTEXITCODE -eq 0) {
            $query | Where-Object { $_ -match "^(TaskName|Status|Last Run|Next Run)" } | ForEach-Object {
                Write-Host "  $_" -ForegroundColor Cyan
            }
        } else {
            Write-Host "  Task '$TaskName' is not registered." -ForegroundColor Red
            Write-Host "  Run: .\hub_task_scheduler.ps1 -Action install" -ForegroundColor Yellow
        }
        $port = if ($env:HUB_PORT) { $env:HUB_PORT } else { "8765" }
        try {
            $h = Invoke-RestMethod "http://localhost:$port/api/health" -TimeoutSec 3 -ErrorAction Stop
            Write-Host "  Hub  : Online - v$($h.version)  uptime $($h.uptime_seconds)s" -ForegroundColor Green
        } catch {
            Write-Host "  Hub  : Not responding on port $port" -ForegroundColor Yellow
        }
    }

    default {
        Write-Host "  Unknown action: '$Action'" -ForegroundColor Red
        Write-Host "  Valid actions: install | remove | restart | status" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host ""
