@echo off
chcp 65001 >nul
echo ============================================================
echo  Recriando .venv limpo para Vulcano2.0
echo ============================================================
echo.

set BACKEND=C:\projetos\Vulcano2.0\backend
set PYTHON=C:\Users\dirfe\AppData\Local\Python\pythoncore-3.14-64\python.exe

echo [1/4] Removendo .venv antigo...
rmdir /s /q "%BACKEND%\.venv"

echo [2/4] Criando novo .venv...
"%PYTHON%" -m venv "%BACKEND%\.venv"

echo [3/4] Instalando dependencias (aguarde, pode demorar 2-3 min)...
"%BACKEND%\.venv\Scripts\pip.exe" install -r "%BACKEND%\requirements.txt" --quiet

echo [4/4] Testando pandas...
"%BACKEND%\.venv\Scripts\python.exe" -c "import pandas; print('pandas OK:', pandas.__version__)"

echo.
echo ============================================================
echo  Concluido! Tente iniciar o backend agora.
echo ============================================================
pause
