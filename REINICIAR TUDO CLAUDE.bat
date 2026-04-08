@echo off
setlocal
title Reiniciando Vulcano2.0 - Claude
color 0A
echo ==============================================================
echo         REINICIANDO VULCANO2.0 (BACK + FRONT)
echo ==============================================================
echo.

set ROOT=C:\projetos\Vulcano2.0
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend
set VENV=%BACKEND%\.venv

echo [1/4] Encerrando processos anteriores...
taskkill /F /FI "WINDOWTITLE eq Vulcano2 - Backend" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Vulcano2 - Frontend" >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/4] Aguardando Windows...
timeout /t 2 /nobreak >nul

echo [3/4] Iniciando Backend (FastAPI - porta 6000)...
start "Vulcano2 - Backend" cmd /k "cd /d "%BACKEND%" && "%VENV%\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 6000 --log-level info"

echo [4/4] Iniciando Frontend (Vite - porta 6001)...
start "Vulcano2 - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:6000 && npm run dev -- --port 6001"

echo.
echo ==============================================================
echo  Tudo iniciado! Aguarde 30s e abra: http://localhost:6001
echo ==============================================================
timeout /t 30 /nobreak >nul
start http://localhost:6001/

endlocal
