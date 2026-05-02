@echo off
setlocal

REM Copia principal (ex.: Antigravity): portas 8002 + 5173.
REM Para Cursor use a pasta vulcano2.0_cursor e start_vulcano2.0_cursor.cmd

set ROOT=C:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend

echo [vulcano2.0] Iniciando backend e frontend...

REM Fecha processos que ocupam as portas 8002 e 5173
for %%P in (8002 5173) do (
  for /f "tokens=5" %%I in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
    taskkill /PID %%I /T /F >nul 2>&1
  )
)

REM Backend (nova janela cmd) - usa python da venv diretamente
start "Questor Backend" cmd /k "cd /d %BACKEND% && if not exist .venv (python -m venv .venv) && .venv\Scripts\python.exe -m pip install -r requirements.txt && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8002 --log-level info"

REM Frontend (nova janela cmd)
start "Questor Frontend" cmd /k "cd /d %FRONTEND% && set VITE_API_BASE=http://127.0.0.1:8002 && if not exist node_modules npm install && npm run dev"

echo [vulcano2.0] Pronto. Abra http://localhost:5173
endlocal
