@echo off
setlocal
title = Subindo Vulcano2.0
echo ==============================================================
echo             INICIANDO VULCANO2.0
echo ==============================================================
echo.

set ROOT=C:\Users\dirfe\Projetos\Vulcano2.0
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend
set VENV=%BACKEND%\.venv

echo [1/3] Iniciando o Backend API (FastAPI - porta 6060)...
start "Vulcano2 - Backend" cmd /k "cd /d "%BACKEND%" && "%VENV%\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 6060 --log-level info"

echo [2/3] Iniciando o Frontend Visual (Vite - porta 6001)...
start "Vulcano2 - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:6060 && npm run dev -- --port 6001"

echo.
echo ==============================================================
echo Aguarde 30s para o backend inicializar, depois acesse:
echo http://localhost:6001
echo ==============================================================
timeout /t 30 /nobreak >nul
start http://localhost:6001/

endlocal
