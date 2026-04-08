@echo off
chcp 65001 >nul
echo Registrando tarefa Vulcano2-AutoCommit...

schtasks /create /tn "Vulcano2-AutoCommit" /xml "%~dp0Vulcano2-AutoCommit.xml" /f

if %errorlevel% == 0 (
    echo.
    echo Tarefa registrada com sucesso!
    echo Rodara a cada 8 horas automaticamente.
    echo.
    schtasks /query /tn "Vulcano2-AutoCommit" /fo LIST
) else (
    echo.
    echo ERRO ao registrar. Tente rodar como Administrador.
)
pause
