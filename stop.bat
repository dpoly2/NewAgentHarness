@echo off
:: AgentHarness — Stop All Services

echo Stopping AgentHarness server and Ollama...

for /f "tokens=2" %%i in ('tasklist ^| findstr "node.exe"') do (
  taskkill /PID %%i /F >nul 2>&1
)
for /f "tokens=2" %%i in ('tasklist ^| findstr "ollama.exe"') do (
  taskkill /PID %%i /F >nul 2>&1
)

echo Done.
pause
