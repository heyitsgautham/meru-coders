@echo off
REM Meru Coders - Development Startup Script
REM Double-click this file to start both backend and frontend

echo ========================================
echo   Meru Coders - Development Server
echo ========================================
echo.

REM Get the current directory
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend
set FRONTEND_DIR=%SCRIPT_DIR%frontend

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        set LOCAL_IP=%%b
        goto :got_ip
    )
)
:got_ip
if "%LOCAL_IP%"=="" set LOCAL_IP=localhost
echo Detected Local IP: %LOCAL_IP%
echo.

REM Start Backend in a new window (with venv activation and PYTHONPATH)
echo [1/2] Starting Backend API server...
start "Meru Coders - Backend" cmd /k "cd /d %BACKEND_DIR% && call venv\Scripts\activate.bat && set PYTHONPATH=%SCRIPT_DIR% && python run.py"

REM Wait for backend to start
echo       Waiting for backend to initialize...
timeout /t 4 /nobreak > nul

REM Start Frontend in a new window with VITE_API_URL set
echo [2/2] Starting Frontend dev server...
REM Set VITE_API_URL so frontend knows where the backend is
start "Meru Coders - Frontend" cmd /k "set PATH=%PATH%;C:\Program Files\nodejs;%APPDATA%\npm && set VITE_API_URL=http://%LOCAL_IP%:5000/api && cd /d %FRONTEND_DIR% && npm run dev -- --host"

REM Wait for frontend to start
timeout /t 2 /nobreak > nul

echo.
echo ========================================
echo   Servers Started Successfully!
echo ========================================
echo.
echo   Local Access:
echo     Frontend:  http://localhost:8080
echo     Backend:   http://localhost:5000/api
echo.
echo   Network Access (for other devices):
echo     Frontend:  http://%LOCAL_IP%:8080
echo     Backend:   http://%LOCAL_IP%:5000/api
echo.
pause
