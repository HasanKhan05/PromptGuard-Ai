$Root = Split-Path -Parent $PSScriptRoot
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$Root\scripts\run-backend.ps1"
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$Root\scripts\run-frontend.ps1"
Write-Host "Started backend and frontend in separate PowerShell windows."
