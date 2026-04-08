@echo off
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Process -NoNewWindow -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
echo "Servidor Reiniciado com o Novo Computo de Acumulado de Contabilizacoes Virtuais!"
