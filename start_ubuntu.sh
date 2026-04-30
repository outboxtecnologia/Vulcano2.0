#!/bin/bash
echo "==========================================="
echo "  INICIANDO VULCANO EXPLORER (UBUNTU LINUX)"
echo "==========================================="

cd "$(dirname "$0")"

echo "[1/3] Verificando servico Firebird (porta 3050)..."
if ! systemctl is-active --quiet firebird3.0; then
    echo "  Iniciando servico Firebird..."
    sudo systemctl start firebird3.0
else
    echo "  Firebird ja esta rodando."
fi

# Matar processos antigos para evitar porta ocupada
echo "Limpando processos nas portas 8000 e 5173..."
fuser -k 8000/tcp >/dev/null 2>&1
fuser -k 5173/tcp >/dev/null 2>&1
sleep 2

echo "[2/3] Iniciando o Backend API (FastAPI)..."
cd backend
source .venv/bin/activate
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > backend_log.txt 2>&1 &
BACKEND_PID=$!
echo "  Backend rodando em background (PID: $BACKEND_PID)"
cd ..

echo "[3/3] Iniciando o Frontend Visual (Vite)..."
cd frontend
export VITE_API_BASE=http://127.0.0.1:8000
nohup npm run dev -- --host > frontend_log.txt 2>&1 &
FRONTEND_PID=$!
echo "  Frontend rodando em background (PID: $FRONTEND_PID)"
cd ..

echo "==========================================="
echo " SISTEMA RODANDO!"
echo " Backend (Porta 8000), Frontend (Porta 5173)"
echo " Logs disponiveis em: backend/backend_log.txt e frontend/frontend_log.txt"
echo " Para parar a aplicacao, execute:"
echo " kill $BACKEND_PID $FRONTEND_PID"
echo "==========================================="
