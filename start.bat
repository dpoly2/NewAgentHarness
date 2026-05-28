@echo off
:: AgentHarness — Quick Launcher (double-click to run)
:: Opens PowerShell and runs start.ps1

cd /d "%~dp0"
powershell.exe -ExecutionPolicy RemoteSigned -NoExit -File "%~dp0start.ps1"
