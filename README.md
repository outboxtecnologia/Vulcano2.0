## Questor Explorer (Questor/Vulcano)

Projeto fullstack:

- **Backend**: FastAPI (porta **8000**)
- **Frontend**: React + Vite (porta **5173**)

## Pré‑requisitos (Windows)

- **Python 3.11+** (recomendado)
- **Node.js 18+**

## Como rodar (modo dev)

Abra 2 terminais.

### Backend

```powershell
cd .\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .\.env.example .\.env
# edite .env e preencha GEMINI_API_KEY
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

Opcional: copie `frontend/.env.example` para `frontend/.env` e ajuste `VITE_API_BASE` (URL do backend que o navegador deve chamar).

```powershell
cd .\frontend
npm install
npm run dev
```

Acesse:

- Frontend: `http://localhost:5173/`
- Backend: `http://127.0.0.1:8000/`
- **Swagger (OpenAPI):** `http://127.0.0.1:8000/docs` — também **ReDoc** em `/redoc` e JSON em `/openapi.json`. A raiz `http://127.0.0.1:8000/` redireciona para `/docs`.

## Parser Python salvo (sem IA)

No fluxo **Universal PDF Generator**, quando você tiver:

- **um modelo selecionado** na barra “Modelos salvos”, ou
- **um padrão por empresa** cadastrado,

a extração manda o PDF para `POST /api/extract-pdf` com `parser_template_id`/`empresa_id` na **query string** e o backend executa o **script Python salvo** (sem Gemini).

## Dados / Banco

- O SQLite fica em `backend/poc_database.sqlite` e contém:
  - `pdf_parser_templates` (scripts `.py` e metadados)
  - `empresa_parser_padrao` (modelo padrão por empresa)

## Docker (Linux / qualquer host com Docker Compose)

O **Firebird não entra na imagem**: configure `FIREBIRD_HOST`, `FIREBIRD_PORT` e `DB_PATH_*` no `backend/.env` com o caminho do `.fdb` **no servidor Firebird remoto**.

```bash
cp backend/.env.example backend/.env   # edite credenciais e host do Firebird
# URL que o navegador usará para chamar a API (ajuste se publicar em outro host):
export VITE_API_BASE=http://localhost:8000
docker compose build
docker compose up -d
```

- API: `http://localhost:8000`
- SPA: `http://localhost:8080`

O SQLite de POC usa volume Docker `poc_sqlite` em `/data/poc_database.sqlite` (variável `POC_DATABASE_FILE` definida no `docker-compose.yml`). Para importar um `poc_database.sqlite` existente, copie para o volume ou troque por *bind mount* comentado no compose.

O frontend lê a URL da API de `VITE_API_BASE` no build (`src/apiBase.js`). Defina `VITE_API_BASE` ao construir a imagem do frontend para o domínio/porta públicos da API.

