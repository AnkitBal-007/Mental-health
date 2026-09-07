# SIH Mental Health Monitoring System - PowerShell Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting SIH Mental Health Monitoring System" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

# 1. Start ML Pipeline
Write-Host "[1/3] Starting ML Pipeline (Port 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\ml-pipeline'; py main.py"

Start-Sleep -Seconds 2

# 2. Start Backend API
Write-Host "[2/3] Starting Backend API (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; py main.py"

Start-Sleep -Seconds 2

# 3. Start Frontend UI
Write-Host "[3/3] Starting Frontend UI (Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "  All services launched in separate windows!" -ForegroundColor Green
Write-Host "  Frontend URL:   http://localhost:3000" -ForegroundColor White
Write-Host "  Backend Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  ML Docs:        http://localhost:8001/docs" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Green
