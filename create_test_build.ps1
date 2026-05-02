$ErrorActionPreference = "Stop"

$source_dir = "c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0"
$target_dir = "c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0_test_build"

Write-Host "Iniciando criacao do Build de Teste. Alvo: $target_dir"

Write-Host "1/3. Compilando Frontend (React Vite)..."
cd $source_dir\frontend
npm run build

Write-Host "2/3. Criando estrutura de diretorios em $target_dir..."
if (Test-Path $target_dir) { Remove-Item -Recurse -Force $target_dir }
New-Item -ItemType Directory -Path $target_dir | Out-Null
New-Item -ItemType Directory -Path "$target_dir\frontend" | Out-Null
New-Item -ItemType Directory -Path "$target_dir\backend" | Out-Null

Write-Host "3/3. Copiando arquivos finais..."
# Copia o build estático do frontend
Copy-Item -Recurse -Path "$source_dir\frontend\dist" -Destination "$target_dir\frontend"

# Copia o backend mas ignora a pasta do ambiente virtual e cache python
Get-ChildItem -Path "$source_dir\backend" | Where-Object { $_.Name -ne "venv" -and $_.Name -ne "__pycache__" } | Copy-Item -Destination "$target_dir\backend" -Recurse -Container

Write-Host "4/4. Criando script inicializador de bateria de testes..."
$start_script = @"
cd backend

# Garante que criamos o venv na maquina final caso não tenha
if (!(Test-Path "venv")) {
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
} else {
    .\venv\Scripts\activate
}

echo "================================================================"
echo " SERVIDOR DE TESTES INICIADO. O FRONTEND ESTA SENDO SERVIDO"
echo " PELO PROPRIO FASTAPI NA PORTA 8000."
echo " ACESSE: http://localhost:8000/"
echo " (Configure o .env nesta pasta para apontar ao banco Questor correto)"
echo "================================================================"

uvicorn main:app --host 0.0.0.0 --port 8000
"@

Set-Content -Path "$target_dir\start_testes.ps1" -Value $start_script

Write-Host "Copia e Exportacao concluidos com SUCESSO!"
