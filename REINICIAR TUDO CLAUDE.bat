@echo off
setlocal
title Vulcano2.0
color 0A

set ROOT=C:\projetos\Vulcano2.0
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend
set VENV=%BACKEND%\.venv

echo Iniciando Backend porta 6000...
start "Vulcano2 - Backend" cmd /k "cd /d "%BACKEND%" && "%VENV%\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 6000 --log-level info"

echo Iniciando Frontend porta 6001...
start "Vulcano2 - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:6000 && npm run dev -- --port 6001"

echo Aguardando 30s... depois abrindo http://localhost:6001
timeout /t 30 /nobreak >nul
start http://localhost:6001/
endlocal
