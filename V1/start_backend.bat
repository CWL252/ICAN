@echo off
rem Start backend inside its virtual environment.
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Run setup_env.bat first to create it.
    pause
    exit /b 1
)

rem Kill any old backend process still holding port 8001
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /c:":8001 " ^| findstr "LISTENING"') do (
    echo Killing old backend process on port 8001, PID: %%p
    taskkill /F /PID %%p >nul 2>&1
)
rem uvicorn --reload spawns a family of processes (reloader, server child,
rem multiprocessing helpers). Killing only one of them leaves the others
rem alive holding the port, so sweep the whole family: every python.exe
rem whose command line mentions uvicorn or the multiprocessing spawn helper
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and ($_.CommandLine -like '*uvicorn*' -or $_.CommandLine -like '*spawn_main*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
ping 127.0.0.1 -n 2 >nul

echo Activating virtual environment: backend\.venv
call ".venv\Scripts\activate.bat"

echo Starting backend at http://127.0.0.1:8001
python -m uvicorn app:app --host 127.0.0.1 --port 8001 --reload

pause
