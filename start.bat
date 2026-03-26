@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   ZouYun Smart Menu System - One-Click Startup (English)
echo ============================================================
echo.

:: 1. Backend Setup
echo [Step 1/3] Setting up Backend...
cd backend

if not exist .env (
    echo [INFO] .env not found, creating from .env.example...
    copy .env.example .env
    echo [IMPORTANT] Please update LLM_API_KEY in backend/.env!
)

echo [INFO] Installing backend dependencies...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo [INFO] Initializing database...
python init_db.py

echo [INFO] Starting Backend server in a new window...
start "ZouYun Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 2. Frontend Setup
echo.
echo [Step 2/3] Setting up Frontend...
cd ..\frontend

if not exist node_modules (
    echo [INFO] node_modules not found, installing dependencies...
    call npm install
)

echo [INFO] Starting Frontend server in a new window...
start "ZouYun Frontend" cmd /k "npm run dev"

:: 3. Finish
echo.
echo [Step 3/3] System Startup Initiated!
echo.
echo ------------------------------------------------------------
echo   Backend API:  http://localhost:8000/docs
echo   Frontend App: http://localhost:5173
echo ------------------------------------------------------------
echo.
echo You can close this window now.
pause
