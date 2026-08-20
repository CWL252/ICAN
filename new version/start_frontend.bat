@echo off
rem Start frontend dev server (Vite).
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [ERROR] node_modules not found.
    echo Run setup_env.bat first to install dependencies.
    pause
    exit /b 1
)

rem Kill any old Vite process still holding port 5180
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /c:":5180 " ^| findstr "LISTENING"') do (
    echo Killing old frontend process on port 5180, PID: %%p
    taskkill /F /PID %%p >nul 2>&1
)
ping 127.0.0.1 -n 2 >nul

echo Starting frontend at http://127.0.0.1:5180
call npm run dev

pause
