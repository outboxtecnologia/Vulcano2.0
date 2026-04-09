# Questor Explorer — Regras do Agente (Antigravity / Jules)

## Stack

- **Backend:** FastAPI + Python, Firebird (Questor + Vulcano), SQLite (poc_database.sqlite)
- **Frontend:** React + Vite (porta 5173), sem proxy — frontend chama backend diretamente
- **IA:** Vertex AI (primário, service account JSON) com fallback para Google AI Studio (GEMINI_API_KEY)
- **Modelo padrão:** `gemini-2.5-flash` via `GEMINI_MODEL` no `.env`

---

## Regras obrigatórias — Vertex AI e Gemini

### SEMPRE fazer

- Verificar `HAS_VERTEXAI` antes de instanciar qualquer modelo. Padrão obrigatório:
  ```python
  model_cls = VertexModel if HAS_VERTEXAI else genai.GenerativeModel
  model = model_cls(GEMINI_MODEL_ID, generation_config=gen_cfg)
  ```
  Nunca chamar `genai.GenerativeModel(...)` diretamente sem essa verificação.

- Incluir `thinking_budget: 0` no `generation_config` quando `HAS_VERTEXAI` é `True`.
  O `gemini-2.5-flash` tem chain-of-thought ativo por padrão no Vertex — desativá-lo economiza 20–60 s por chamada sem perda de qualidade para extração estruturada.

- Incluir `max_output_tokens` no `generation_config` para evitar respostas runaway.

- `_require_gemini_key()` deve ter bypass quando Vertex está disponível:
  ```python
  def _require_gemini_key():
      if HAS_VERTEXAI:
          return  # Vertex usa service account JSON, não precisa de API key
      if not os.environ.get("GEMINI_API_KEY"):
          raise HTTPException(status_code=500, detail="GEMINI_API_KEY não configurada")
  ```

- Usar `_gemini_generate_json_async` (assíncrona) dentro de endpoints `async def`.
  Se precisar da versão síncrona dentro de `async def`, usar:
  ```python
  await asyncio.to_thread(_gemini_generate_json, prompt)
  ```

Bloco padrão de `generation_config`:
```python
gen_cfg = {
    "response_mime_type": "application/json",
    "max_output_tokens": 8192,
}
if HAS_VERTEXAI:
    gen_cfg["thinking_config"] = {"thinking_budget": 0}
```

---

## Regras obrigatórias — Extração de PDF

### SEMPRE fazer

- Executar `pdfplumber` dentro de `asyncio.to_thread` — nunca chamar diretamente em endpoint `async def`:
  ```python
  def _extract_pages(raw: bytes) -> list[str]:
      result = []
      with pdfplumber.open(io.BytesIO(raw)) as pdf:
          for i, page in enumerate(pdf.pages):
              if i >= max_pages: break
              extracted = page.extract_text() or page.extract_text(layout=True) or ""
              if extracted.strip():
                  result.append(f"--- Página {i + 1} ---\n{extracted[:max_chars]}")
      return result

  chunks = await asyncio.to_thread(_extract_pages, content)
  ```

- Usar `page.extract_text()` (sem `layout=True`) como chamada principal.
  `layout=True` é ~10x mais lento — usar só como fallback quando retornar vazio.

- Manter `max_chars` por página em **4 500** ou menos.

- Disparar todas as páginas em paralelo com `asyncio.gather` — nunca processar páginas em loop sequencial.

- Manter `asyncio.Semaphore` para controlar rate-limit do Vertex.

### Prompts de extração

- Manter prompts compactos: schema JSON em variável string separada, depois interpolar no f-string.
- Nunca usar `\"` escapado dentro de f-string com aspas simples no Python 3.12+ — causa `SyntaxError: unterminated f-string`.

Padrão correto:
```python
schema = '{"registros":[{"comprador":"","cpf_cnpj":"","valor_raiz":0.0}]}'
prompt = f"Extraia recebimentos. Retorne apenas JSON:\n{schema}\n\n{chunk_text}"
```

---

## Regras obrigatórias — Dados contábeis

- `contas_fisicas_empresa` é calculada **uma vez, empresa-wide**. Ao montar a resposta de `/api/questor/contabilizacoes`, incluir `contas_fisicas` apenas no **primeiro** empreendimento do array:
  ```python
  eh_primeiro = len(resultados) == 0
  resultados.append({
      ...
      "contas_fisicas": list(contas_fisicas.values()) if eh_primeiro else [],
      "contas_virtuais": list(contas_virtuais.values())
  })
  ```
  O frontend acumula via `merge()` — repetir o bloco físico N vezes multiplica o saldo por N.

---

## PROIBIDO

- `genai.GenerativeModel(...)` sem verificar `HAS_VERTEXAI` antes — incluindo em funções auxiliares como `_gemini_generate_python_plain`.
- Omitir `thinking_config: {thinking_budget: 0}` em chamadas Vertex com `gemini-2.5-flash`.
- `pdfplumber` chamado diretamente em endpoint `async def` fora de `asyncio.to_thread`.
- `page.extract_text(layout=True)` como chamada principal (só como fallback).
- `max_chars` acima de **5 000** por chunk de página.
- Processar páginas do PDF em loop sequencial — sempre `asyncio.gather`.
- `_gemini_generate_json` (síncrona) chamada diretamente dentro de `async def`.
- Retornar `contas_fisicas` repetido para cada empreendimento no response de contabilizações.
- `_require_gemini_key()` bloqueando quando `HAS_VERTEXAI` é `True`.
- f-strings com `\"` escapado dentro de aspas simples — usar variável intermediária.
- Subir backend sem verificar sintaxe antes:
  ```
  .venv\Scripts\python.exe -c "import main; print('syntax OK')"
  ```

---

## Portas e inicialização

| Serviço | Porta | Script |
|---|---|---|
| Backend FastAPI | 8000 | `1_Subir_Questor_Explorer.bat` |
| Frontend Vite | 5173 | `1_Subir_Questor_Explorer.bat` |
| Firebird | 3050 | serviço Windows |

Antes de qualquer push ou entrega, verificar sintaxe do backend:
```
cd backend && .venv\Scripts\python.exe -c "import main; print('syntax OK')"
```

---

## Relação com Vulcano 2.0

Este projeto é o **original** do qual `C:\Projetos\Vulcano2.0` foi derivado.
Ambos compartilham a mesma arquitetura de backend (FastAPI + Firebird) e as mesmas regras de IA acima.
Mudanças de performance ou correções aplicadas em um devem ser avaliadas para o outro.
