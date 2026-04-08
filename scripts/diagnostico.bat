@echo off
cd /d C:\projetos\Vulcano2.0\backend
echo Rodando diagnostico de startup...
echo Se travar em algum numero, esse e o problema.
echo.
.venv\Scripts\python.exe diag_startup.py
echo.
pause
