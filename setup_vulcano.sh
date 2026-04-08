#!/bin/bash
echo "==========================================="
echo "  SETUP E INICIALIZACAO: VULCANO EXPLORER"
echo "==========================================="

cd "$(dirname "$0")"

echo "[1/4] Verificando/Instalando dependencias do Backend (Python)..."
cd backend
if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual..."
    python -m venv .venv
fi
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || echo "Aviso: Nao foi possivel ativar o .venv"
echo "Instalando requirements.txt..."
pip install -r requirements.txt
echo "Dependencias garantidas! Iniciando FastAPI na porta 8000..."
start "Vulcano Backend" cmd /k "python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload" &
cd ..

echo "[2/4] Instalando dependencias do Frontend (Node.js)..."
cd frontend
npm install
echo "[3/4] Iniciando Servidor Frontend na porta 5173..."
start "Vulcano Frontend" cmd /k "npm run dev" &
cd ..

echo "[4/4] Aguardando servicos subirem..."
sleep 5

start http://localhost:5173/ 2>/dev/null || xdg-open http://localhost:5173/ 2>/dev/null || open http://localhost:5173/ 2>/dev/null

echo "Sucesso! Sistema configurado e rodando."
