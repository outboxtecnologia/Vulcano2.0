@echo off
setlocal
title = Subindo Vulcano2.0
echo ==============================================================
echo             INICIANDO VULCANO2.0
echo ==============================================================
echo.

set ROOT=C:\projetos\Vulcano2.0
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend
set VENV=%BACKEND%\.venv

echo [1/3] Encerrando processos na porta 6000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":6000 " 2^>nul') do taskkill /F /PID %%a >nul 2>&1
timeout /t 3 >nul

echo [2/3] Iniciando o Backend API (FastAPI - porta 6000)...
start "Vulcano2 - Backend" cmd /k "cd /d "%BACKEND%" && "%VENV%\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 6000 --log-level info"

echo [3/3] Iniciando o Frontend Visual (Vite - porta 6001)...
start "Vulcano2 - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:6000 && npm run dev -- --port 6001"

echo.
echo ==============================================================
echo CONCLUIDO! Abrindo http://localhost:6001
echo ==============================================================
timeout /t 6 >nul
start http://localhost:6001/

endlocal
