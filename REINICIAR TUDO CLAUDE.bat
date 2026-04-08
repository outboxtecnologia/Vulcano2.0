@echo off
setlocal
title Reiniciando Vulcano2.0 - Claude
color 0A
echo ==============================================================
echo         REINICIANDO VULCANO2.0 (BACK + FRONT)
echo ==============================================================
echo.

set ORIG=C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend
set NEW_BACKEND=C:\projetos\Vulcano2.0\backend
set FRONTEND=C:\projetos\Vulcano2.0\frontend
set VENV=%ORIG%\.venv

echo [1/4] Encerrando processos nas portas 6000 e 6001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":6000 " 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":6001 " 2^>nul') do taskkill /F /PID %%a >nul 2>&1

echo [2/4] Aguardando Windows...
timeout /t 3 /nobreak >nul

echo [3/4] Iniciando Backend (FastAPI - porta 6000)...
start "Vulcano2 - Backend" cmd /k "cd /d "%ORIG%" && "%VENV%\Scripts\python.exe" -m uvicorn main:app --app-dir "%NEW_BACKEND%" --host 127.0.0.1 --port 6000 --log-level info"

echo [4/4] Iniciando Frontend (Vite - porta 6001)...
start "Vulcano2 - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:6000 && npm run dev -- --port 6001"

echo.
echo ==============================================================
echo  Tudo iniciado! Abrindo navegador em 6 segundos...
echo ==============================================================
timeout /t 6 /nobreak >nul
start http://localhost:6001/

endlocal
