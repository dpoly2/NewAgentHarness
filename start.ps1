# AgentHarness - Startup Script
# Run from repo root: .\start.ps1

$ROOT = $PSScriptRoot
$APP  = "$ROOT\projects\agentharness-v2"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AgentHarness v2 - Starting Up" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Ollama
$ollamaRunning = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($ollamaRunning) {
  Write-Host "(OK) Ollama already running (PID $($ollamaRunning.Id))" -ForegroundColor Green
} else {
  $ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
  if (Test-Path $ollamaExe) {
    Write-Host "(..) Starting Ollama..." -ForegroundColor Yellow
    Start-Process $ollamaExe -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "(OK) Ollama started" -ForegroundColor Green
  } else {
    Write-Host "(!!) Ollama not found - skipping (chat AI unavailable)" -ForegroundColor Red
  }
}

# 2. AgentHarness Server
$serverUp = $false
try { Invoke-RestMethod "http://localhost:4000/api/health" -ErrorAction Stop | Out-Null; $serverUp = $true } catch {}

if ($serverUp) {
  Write-Host "(OK) Server already running on port 4000" -ForegroundColor Green
} else {
  Write-Host "(..) Starting AgentHarness server on port 4000..." -ForegroundColor Yellow
  $nodePath = (Get-Command node -ErrorAction SilentlyContinue).Source
  if (-not $nodePath) { $nodePath = "C:\Program Files\nodejs\node.exe" }
  Start-Process $nodePath -ArgumentList "core/server.js" -WorkingDirectory $APP -WindowStyle Hidden
  Start-Sleep -Seconds 5
  try {
    $health = Invoke-RestMethod "http://localhost:4000/api/health" -ErrorAction Stop
    Write-Host "(OK) Server running - status: $($health.status), v$($health.version)" -ForegroundColor Green
  } catch {
    Write-Host "(!!) Server did not respond - check logs in projects/agentharness-v2/logs/" -ForegroundColor Red
  }
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "  App:   http://localhost:4000" -ForegroundColor White
Write-Host "  Login: admin / AH2026" -ForegroundColor White
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host ""