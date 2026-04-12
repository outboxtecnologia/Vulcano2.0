@echo off
setlocal
title Subindo Questor Explorer
echo ==============================================================
echo             INICIANDO QUESTOR EXPLORER
echo ==============================================================
echo.

set ROOT=C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend

echo [1/3] Encerrando processos antigos nas portas 8000 e 5173...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo   Matando PID %%p na porta 8000...
    taskkill /PID %%p /F >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    echo   Matando PID %%p na porta 5173...
    taskkill /PID %%p /F >nul 2>&1
)
echo Aguardando portas serem liberadas...
timeout /t 3 >nul

echo [2/3] Iniciando o Backend API (FastAPI)...
start "Questor - Backend" cmd /k "cd /d "%BACKEND%" && .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info"

echo [3/3] Iniciando o Frontend Visual (Vite)...
start "Questor - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:8000 && npm run dev"

echo.
echo ==============================================================
echo CONCLUIDO! O navegador vai abrir em instantes.
echo ==============================================================
timeout /t 6 >nul
start http://localhost:5173/

endlocal
