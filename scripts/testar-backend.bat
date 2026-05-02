@echo off
title Vulcano2 - Diagnostico
color 0E
echo Testando imports do backend...
echo.

set VENV=C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\.venv

"%VENV%\Scripts\python.exe" "C:\projetos\Vulcano2.0\backend\diag_startup.py"

echo.
echo Se chegou aqui, imports OK. Tentando subir uvicorn...
echo.

cd /d C:\projetos\Vulcano2.0\backend
"%VENV%\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 6000 --log-level info

pause
