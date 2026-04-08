@echo off
cd /d C:\projetos\Vulcano2.0\backend
echo Testando backend na porta 6000...
echo Se aparecer "Application startup complete" esta funcionando.
echo.
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 6000 --log-level info
pause
