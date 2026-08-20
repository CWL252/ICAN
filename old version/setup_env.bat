@echo off
rem Recreate all dependencies from scratch:
rem   - backend: delete .venv, recreate, install requirements.txt
rem   - frontend: delete node_modules, npm install
cd /d "%~dp0"

echo ============================================
echo [1/2] Backend: rebuilding virtual environment
echo ============================================
if exist "backend\.venv" rmdir /s /q "backend\.venv"
python -m venv "backend\.venv" || goto :error
"backend\.venv\Scripts\python.exe" -m pip install --upgrade pip || goto :error
echo Installing torch/torchvision (CPU build)...
"backend\.venv\Scripts\python.exe" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu || goto :error
echo Installing remaining backend dependencies...
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt" || goto :error

echo.
echo ============================================
echo [2/2] Frontend: reinstalling node_modules
echo ============================================
if exist "frontend\node_modules" rmdir /s /q "frontend\node_modules"
pushd frontend
call npm install || goto :error
popd

echo.
echo All dependencies installed.
echo Start the app with start_backend.bat and start_frontend.bat
pause
exit /b 0

:error
echo.
echo [ERROR] Setup failed. See messages above.
pause
exit /b 1
