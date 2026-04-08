@echo off
setlocal
title = Reiniciando Questor Explorer
echo ==============================================================
echo             REINICIANDO QUESTOR EXPLORER
echo ==============================================================
echo.

set ROOT=C:\projetos\Vulcano2.0
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend

echo [1/3] Matando processos nas portas 6000 e 6001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":6000 " 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":6001 " 2^>nul') do taskkill /F /PID %%a >nul 2>&1

echo Aguardando as portas serem liberadas pelo Windows...
timeout /t 3 >nul

echo [2/3] Iniciando o Backend API (FastAPI)...
start "Questor - Backend" cmd /k "cd /d "%BACKEND%" && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 6000 --log-level info"

echo [3/3] Iniciando o Frontend Visual (Vite)...
start "Questor - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:6000 && npm run dev -- --port 6001"

echo.
echo ==============================================================
echo CONCLUIDO! O navegador vai abrir em instantes.
echo ==============================================================
timeout /t 6 >nul
start http://localhost:6001/

endlocal
