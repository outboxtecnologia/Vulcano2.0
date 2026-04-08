@echo off
setlocal
title Reiniciando Questor Explorer - Claude
color 0A
echo ==============================================================
echo         REINICIANDO QUESTOR EXPLORER (BACK + FRONT)
echo ==============================================================
echo.

set ROOT=C:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend

echo [1/4] Encerrando processos antigos (Ignorado)...

echo [2/4] Aguardando Windows...
timeout /t 3 /nobreak >nul

echo [3/4] Iniciando Backend (FastAPI)...
start "Questor - Backend" cmd /k "cd /d "%BACKEND%" && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8080 --log-level info"

echo [4/4] Iniciando Frontend (Vite)...
start "Questor - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:8080 && npm run dev"

echo.
echo ==============================================================
echo  Tudo iniciado! Abrindo navegador em 6 segundos...
echo ==============================================================
timeout /t 6 /nobreak >nul
start http://localhost:5173/

endlocal
