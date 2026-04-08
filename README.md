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

```powershell
cd .\frontend
npm install
npm run dev
```

Acesse:

- Frontend: `http://localhost:5173/`
- Backend: `http://127.0.0.1:8000/`

## Parser Python salvo (sem IA)

No fluxo **Universal PDF Generator**, quando você tiver:

- **um modelo selecionado** na barra “Modelos salvos”, ou
- **um padrão por empresa** cadastrado,

a extração manda o PDF para `POST /api/extract-pdf` com `parser_template_id`/`empresa_id` na **query string** e o backend executa o **script Python salvo** (sem Gemini).

## Dados / Banco

- O SQLite fica em `backend/poc_database.sqlite` e contém:
  - `pdf_parser_templates` (scripts `.py` e metadados)
  - `empresa_parser_padrao` (modelo padrão por empresa)

