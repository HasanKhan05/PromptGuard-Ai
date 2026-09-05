$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "[1/3] Backend tests"
Set-Location "$Root\backend"
& ".\.venv\Scripts\python.exe" -m pytest -q

Write-Host "[2/3] Frontend lint"
Set-Location "$Root\frontend"
npm run lint

Write-Host "[3/3] Frontend build"
npm run build

Set-Location $Root
Write-Host "Foundation verification passed." -ForegroundColor Green
