#!/bin/bash
echo "==========================================="
echo "  SETUP: VULCANO EXPLORER (UBUNTU LINUX)"
echo "==========================================="

cd "$(dirname "$0")"

echo "[1/4] Instalando dependencias do sistema (Python, Node.js, Firebird)..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip curl software-properties-common

# Instalar Node.js via NodeSource (versão 20 LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Instalar Firebird
sudo apt-get install -y firebird3.0-server firebird-dev

echo "[2/4] Configurando Backend (Python)..."
cd backend
if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo "Instalando dependencias (requirements.txt)..."
pip install -r requirements.txt
cd ..

echo "[3/4] Configurando Frontend (Node.js)..."
cd frontend
npm install
cd ..

echo "==========================================="
echo " SETUP CONCLUIDO COM SUCESSO!"
echo " Para iniciar o sistema, execute: ./start_ubuntu.sh"
echo "==========================================="
