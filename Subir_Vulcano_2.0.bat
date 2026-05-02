@echo off
setlocal
title Subindo Vulcano 2.0
color 0C

echo ==============================================================================
echo.
echo  ##     ## ##     ## ##        ######     ###    ##    ##  #######   #######   #####  
echo  ##     ## ##     ## ##       ##    ##   ## ##   ###   ## ##     ## ##     ## ##   ## 
echo  ##     ## ##     ## ##       ##        ##   ##  ####  ## ##     ##        ## ##   ## 
echo  ##     ## ##     ## ##       ##       ##     ## ## ## ## ##     ##  #######  ##   ## 
echo   ##   ##  ##     ## ##       ##       ######### ##  #### ##     ## ##        ##   ## 
echo    ## ##   ##     ## ##       ##    ## ##     ## ##   ### ##     ## ##        ##   ## 
echo     ###     #######  ########  ######  ##     ## ##    ##  #######  #########  #####  
echo.
echo ==============================================================================
echo.

set ROOT=C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend
set FIREBIRD_BIN=C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\Firebird\bin

echo [0/3] Verificando servico Firebird (porta 3050)...
netstat -aon | findstr ":3050 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   Firebird NAO esta rodando. Iniciando fbserver.exe...
    start "Firebird Server" /MIN "%FIREBIRD_BIN%\fbserver.exe" -a
    timeout /t 3 >nul
    netstat -aon | findstr ":3050 " | findstr "LISTENING" >nul 2>&1
    if errorlevel 1 (
        echo   [AVISO] Firebird pode nao ter iniciado. Verifique se o arquivo existe em:
        echo   %FIREBIRD_BIN%\fbserver.exe
    ) else (
        echo   Firebird iniciado com sucesso na porta 3050.
    )
) else (
    echo   Firebird ja esta rodando na porta 3050. OK.
)
echo.

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
start "Vulcano 2.0 - Backend" cmd /k "cd /d "%BACKEND%" && .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info"

echo [3/3] Iniciando o Frontend Visual (Vite)...
start "Vulcano 2.0 - Frontend" cmd /k "cd /d "%FRONTEND%" && set VITE_API_BASE=http://127.0.0.1:8000 && npm run dev"

echo.
echo ==============================================================
echo CONCLUIDO! O navegador vai abrir em instantes.
echo ==============================================================
timeout /t 6 >nul
start http://localhost:5173/

endlocal
