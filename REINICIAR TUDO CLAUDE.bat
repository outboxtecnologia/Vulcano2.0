@echo off
setlocal
title Vulcano2.0
color 0A

set ORIG=C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend
set NEW=C:\projetos\Vulcano2.0\backend
set FRONTEND=C:\projetos\Vulcano2.0\frontend
set VENV=%ORIG%\.venv

echo Iniciando Backend porta 6000 (codigo: Vulcano2.0)...
start "Vulcano2 - Backend" cmd /k "cd /d "%ORIG%" && "%VENV%\Scripts\python.exe" -m uvicorn main:app --app-dir "%NEW%" --host 127.0.0.1 --port 6000 --log-level info"

echo Iniciando Frontend porta 6001...
start "Vulcano2 - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:6000 && npm run dev -- --port 6001"

echo Aguardando 15s e abrindo http://localhost:6001
timeout /t 15 /nobreak >nul
start http://localhost:6001/
endlocal
