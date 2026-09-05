$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location "$Root\frontend"
npm install
if (-not (Test-Path ".env.local")) { Copy-Item ".env.local.example" ".env.local" }
Write-Host "Frontend setup complete." -ForegroundColor Green
