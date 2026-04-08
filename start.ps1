$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host "[vulcano2.0] $msg" -ForegroundColor Cyan }

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

if (!(Test-Path $backend)) { throw "Pasta backend não encontrada: $backend" }
if (!(Test-Path $frontend)) { throw "Pasta frontend não encontrada: $frontend" }

Write-Info "Iniciando backend e frontend em janelas separadas..."

# --- BACKEND ---
$venv = Join-Path $backend ".venv"
$activate = Join-Path $venv "Scripts\Activate.ps1"
$requirements = Join-Path $backend "requirements.txt"
$envFile = Join-Path $backend ".env"
$envExample = Join-Path $backend ".env.example"

$backendCmd = @"
Set-Location "$backend"
if (!(Test-Path "$venv")) { python -m venv ".venv" }
& "$activate"
if (Test-Path "$requirements") { pip install -r "$requirements" }
if (!(Test-Path "$envFile") -and (Test-Path "$envExample")) { Copy-Item "$envExample" "$envFile" }
if (Test-Path "$envFile") {
  $envText = Get-Content "$envFile" -Raw
  if ($envText -match '^\s*GEMINI_API_KEY\s*=\s*$' -or $envText -notmatch '^\s*GEMINI_API_KEY\s*=\s*\S+' ) {
    Write-Host '[vulcano2.0] ATENÇÃO: GEMINI_API_KEY está vazia no backend/.env (a extração por IA não vai funcionar).' -ForegroundColor Yellow
  }
} else {
  Write-Host '[vulcano2.0] ATENÇÃO: backend/.env não encontrado. Crie a partir de .env.example e preencha GEMINI_API_KEY.' -ForegroundColor Yellow
}

# Libera a porta 8002 antes de subir o uvicorn (evita ficar preso em processos antigos/reloaders).
try {
  $listeners = Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue
  if ($listeners) {
    $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($p in $pids) {
      if ($p) {
        Write-Host "[vulcano2.0] Finalizando processo na porta 8002 (PID=$p)..." -ForegroundColor Yellow
        try { taskkill /PID $p /T /F | Out-Null } catch {}
        try { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue } catch {}
      }
    }
  }
} catch {}

# Aguarda a porta liberar (até 5s)
for ($i = 0; $i -lt 25; $i++) {
  $still = Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue
  if (!$still) { break }
  Start-Sleep -Milliseconds 200
}
if (Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue) {
  Write-Host "[vulcano2.0] ATENÇÃO: ainda existe algo escutando na porta 8002. O backend pode não iniciar." -ForegroundColor Red
}

# Evita travamentos do reload/watchfiles em algumas máquinas: subimos sem --reload.
python -m uvicorn main:app --host 127.0.0.1 --port 8002 --log-level info
"@

Start-Process -FilePath "powershell.exe" -ArgumentList @(
  "-NoProfile",
  "-NoExit",
  "-ExecutionPolicy", "Bypass",
  "-Command", $backendCmd
)

# --- FRONTEND ---
$frontendCmd = @"
Set-Location "$frontend"
# Garante que o Vite pegue o backend correto mesmo sem reiniciar manualmente.
$env:VITE_API_BASE = 'http://127.0.0.1:8002'

# Libera a porta 5173 (Vite) antes de subir.
try {
  $listeners = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
  if ($listeners) {
    $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($p in $pids) {
      if ($p) {
        Write-Host "[vulcano2.0] Finalizando processo na porta 5173 (PID=$p)..." -ForegroundColor Yellow
        try { taskkill /PID $p /T /F | Out-Null } catch {}
        try { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue } catch {}
      }
    }
  }
} catch {}

if (!(Test-Path "node_modules")) { npm install }
npm run dev
"@

Start-Process -FilePath "powershell.exe" -ArgumentList @(
  "-NoProfile",
  "-NoExit",
  "-ExecutionPolicy", "Bypass",
  "-Command", $frontendCmd
)

Write-Info "Pronto. Abra http://localhost:5173/ (frontend)."

