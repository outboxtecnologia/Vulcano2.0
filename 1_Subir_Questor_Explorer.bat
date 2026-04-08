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
set VENV=C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\.venv

echo [1/3] Limpando processos antigos (Ignorado)...

echo Aguardando as portas serem liberadas pelo Windows...
timeout /t 3 >nul

echo [2/3] Iniciando o Backend API (FastAPI)...
start "Vulcano2 - Backend" cmd /k "cd /d "%BACKEND%" && "%VENV%\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 6000 --log-level info"

echo [3/3] Iniciando o Frontend Visual (Vite)...
start "Vulcano2 - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:6000 && npm run dev -- --port 6001"

echo.
echo ==============================================================
echo CONCLUIDO! O navegador vai abrir em instantes.
echo ==============================================================
timeout /t 6 >nul
start http://localhost:6001/

endlocal
