# Documentação e Regras de APIs e Integração - Questor Explorer

> [!WARNING]
> **REGRA DE AUTORIZAÇÃO GLOBAL:** Ações (ou agentes IA) em sessão *NUNCA* devem alterar ou recriar lógicas relacionadas a **Caminhos de Arquivos (Paths)**, **Cotas/Limites (Semáforos)** ou **Tokens de Acesso (API Keys/Chaves JSON)** no repositório sem antes solicitar permissão explícita ou relatar a intenção ao usuário principal via chat. Toda modificação na infraestrutura core de conexão depende de "Sinal Verde".

Este documento descreve as regras de ouro de engenharia do backend do Questor Explorer no que tange a serviços de inteligência artificial de terceiros e consultas em lote.

## 1. Integração com IA (Modelos Google / Gemini)

**REGRA ESTRITA:** Todas as integrações de extração paralela em documentos com os motores de IA do Google *DEVEM* ser concebidas utilizando **Vertex AI** via **Chave JSON (Service Account)**.

### O Motivo
O projeto precisa quebrar grandes documentos PDF em *Parallel Gathers* com concorrência nativa. Chamar as rotas estendidas pelo `google.generativeai` (AI Studio - MakerSuite API KEYS) provocará expropriação sistemática em formato *HTTP 429 - Too Many Requests / ResourceExhausted*. A chave JSON (`chavejson.json`) garante vazões corporativas dentro de cotas alocadas transparentes vinculadas ao projeto do Google Cloud.

### Práticas de Código (Como está mapeado)
1. **Bibliotecas Padrão:** Não instancie `genai.GenerativeModel(...)` para processamento paralelo puro. O projeto suporta um seletor unificado no `main.py`: `VertexModel` vs `genai`. Priorize as rotinas `_gemini_generate_json_async`.
2. **Ambiente:** A autenticação ocorre por meio da passiva leitura da variável `GOOGLE_APPLICATION_CREDENTIALS`. O `.env` deve obrigatoriamente apontará para este JSON local.
3. **Inicialização do SDK:**
   ```python
   import vertexai
   from vertexai.generative_models import GenerativeModel, Part

   # Usa a infraestrutura GCP vinculada ao chavejson
   vertexai.init(project="questor-explorer-prod", location="us-central1")
   ```
4. **Visão e Anexos:** Sempre utilize o tipo literal `Part.from_data(mime_type=..., data=...)` em interações multimodais na library do Vertex; arrays simples de interface não são perfeitamente amparados de forma estável lá.

## 2. Assincronia e Firebird (Otimizações Locais)
Além da proteção do lado da nuvem, a interface de Conciliação e Smart Preview obedecerá às seguintes balizas para não afogar o Firebird local e as interações com API Rest:

* **Semaforização Assíncrona:** Tarefas concorrentes enviadas ao Vertex jamais devem voar "soltas" no gather. Utilize `asyncio.Semaphore()` configurado com limite estrito baixo (ex: `Semaphore(2)`) acoplando controle de vazão natural.
* **Janelas Temporais em Buffer Memória:** Evite `cur.execute` cíclicos de Select sem `WHERE` de data de corte. Motor de conciliação (onde há verificação diária de pagamentos passados x futuros) deve possuir, estritamente, cláusulas do tipo `WHERE p.DATA >= '2025-06-01'` barrando a entrada de logs pregressos antiquíssimos na memória principal do servidor.
