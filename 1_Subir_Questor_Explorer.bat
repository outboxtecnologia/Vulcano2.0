@echo off
setlocal
title = Subindo Questor Explorer
echo ==============================================================
echo             INICIANDO QUESTOR EXPLORER
echo ==============================================================
echo.

set ROOT=C:\projetos\Vulcano2.0
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend

echo [1/3] Limpando processos antigos (Ignorado)...

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
