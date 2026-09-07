@echo off
TITLE SIH Project 1 - Launcher
echo ===================================================
echo   Starting SIH Mental Health Monitoring System
echo ===================================================
echo.

echo [1/3] Starting ML Pipeline (Port 8001)...
start "ML Pipeline - Port 8001" cmd /k "cd /d %~dp0ml-pipeline && py main.py"

timeout /t 2 /nobreak >nul

echo [2/3] Starting Backend API (Port 8000)...
start "Backend API - Port 8000" cmd /k "cd /d %~dp0backend && py main.py"

timeout /t 2 /nobreak >nul

echo [3/3] Starting Frontend UI (Port 3000)...
start "Frontend UI - Port 3000" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ===================================================
echo   All 3 services are launching in separate windows!
echo   Frontend URL:  http://localhost:3000
echo   Backend Docs:  http://localhost:8000/docs
echo   ML Docs:       http://localhost:8001/docs
echo ===================================================
echo.
pause
