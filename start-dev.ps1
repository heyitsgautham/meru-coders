#!/usr/bin/env pwsh
# Meru Coders - Development Startup Script
# Starts both backend and frontend for local development

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Meru Coders - Development Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"

# Get local IP address
$LocalIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notmatch '^169\.' -and $_.IPAddress -ne '127.0.0.1' } | Select-Object -First 1).IPAddress
if (-not $LocalIP) { $LocalIP = "localhost" }

Write-Host "Detected Local IP: $LocalIP" -ForegroundColor Green
Write-Host ""

# Check if directories exist
if (-not (Test-Path $BackendDir)) {
    Write-Host "ERROR: Backend directory not found at $BackendDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $FrontendDir)) {
    Write-Host "ERROR: Frontend directory not found at $FrontendDir" -ForegroundColor Red
    exit 1
}

# Start Backend in a new PowerShell window (with venv activation)
Write-Host "[1/2] Starting Backend API server..." -ForegroundColor Yellow
$backendCmd = "cd '$BackendDir'; .\venv\Scripts\Activate.ps1; `$env:PYTHONPATH='$ScriptDir'; python run.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# Wait for backend to start
Write-Host "      Waiting for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 4

# Start Frontend in a new PowerShell window with VITE_API_URL set
Write-Host "[2/2] Starting Frontend dev server..." -ForegroundColor Yellow
# Set VITE_API_URL so frontend knows where the backend is
$frontendCmd = "`$env:PATH = `$env:PATH + ';C:\Program Files\nodejs;' + `$env:APPDATA + '\npm'; `$env:VITE_API_URL = 'http://${LocalIP}:5000/api'; cd '$FrontendDir'; npm run dev -- --host"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

# Wait for frontend to start
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Servers Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Local Access:" -ForegroundColor Yellow
Write-Host "    Frontend:  http://localhost:8080" -ForegroundColor White
Write-Host "    Backend:   http://localhost:5000/api" -ForegroundColor White
Write-Host ""
Write-Host "  Network Access (for other devices):" -ForegroundColor Yellow
Write-Host "    Frontend:  http://${LocalIP}:8080" -ForegroundColor Green
Write-Host "    Backend:   http://${LocalIP}:5000/api" -ForegroundColor Green
Write-Host ""
Write-Host "  Press any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
