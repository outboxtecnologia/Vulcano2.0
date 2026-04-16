import os
import json

base_dir = r"docs\MOCs\Deep_Dives\Fluxo_Auditoria"
os.makedirs(base_dir, exist_ok=True)

v_geral = '''# O Fluxo de Auditoria e Conciliação
Este é o coração do sistema Smart Importer + Auditoria ERP.
Abaixo você encontra o detalhamento a nível de código-fonte de cada etapa da máquina.

Use o Canvas do Obsidian Lousa_Fluxo_Auditoria_Arquitetura.canvas para ver as conexões entre esses documentos.
'''

v_vertex = '''# 1. Prompt Vertex AI e Extração (main.py)
A IA Generativa (gemini-2.5-flash) é usada unicamente como "Transcritor Semântico de OCR". O código em Python recorta o PDF com pdfplumber e joga numa string formatada f-string para a porta do Vertex.

**O Prompt Python Exato usado no sistema:**
`python
prompt = f\"\"\"Você extrai linhas de RECEBIMENTOS/PAGAMENTOS/PARCELAS de relatórios imobiliários.
Restaure a semântica de colunas tabulares.

SCHEMA:
1. 'comprador': Nome do cliente.
2. 'cpf_cnpj': CPF ou CNPJ.
3. 'empreendimento': Nome do prédio/projeto.
4. 'unidade': Número do apartamento/lote.
5. 'dt_vencimento': Data original de corte.
6. 'dt_pagamento': Data da baixa no banco.
7. 'parcela': Número (ex: 12/41 PM).
8. Numéricos (float): 'valor_raiz', 'descontos', 'acrescimos_variacoes' (Juros+Multa+Tx), 'total_pago' (Líquido). Se nulo, 0.0.

SAÍDA (APENAS JSON VÁLIDO):
{{
  "registros": [
    {{ "comprador": "...", "cpf_cnpj": "...", "empreendimento": "...", "unidade": "...", "dt_vencimento": "...", "dt_pagamento": "...", "parcela": "...", "valor_raiz": 0.0, "descontos": 0.0, "acrescimos_variacoes": 0.0, "total_pago": 0.0 }}
  ]
}}
Não inclua texto fora do JSON. Traga TODAS as linhas encontradas.

Text extraído:
{header_ctx}
{chunk_text}
\"\"\"
`

**Configurações do Vertex no Código:**
O sistema está programado para 	hinking_budget: 0 e esponse_mime_type: application/json no backend para extirpar "devaneios" da IA e obter o JSON instântaneamente.
'''

v_pandas = '''# 2. Vetorização com Pandas (main.py)
O JSON retornado do Vertex é convertido imediatamente em pd.DataFrame. Fazer loops normais mataria a CPU para limpeza de dados.

**Aceleradores de Código no API do Vulcano:**
`python
# df é preenchido com a query bruta do Firebird ou da IA
df = pd.read_sql_query(query, conn, params=tuple(params))

# Vetorização de formatação de nulos para o JSON do FastAPI não engasgar:
df = df.replace({np.nan: None})

# Tratamento Temporal (Isso resolve Bugs de UI no React instantaneamente)
df['DATA_STR'] = pd.to_datetime(df['DATA'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
df['DATA_ISO'] = pd.to_datetime(df['DATA'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
`
> O backend despacha encimento_iso (para a matemática do < do Javascript operar perfeitamente no *Filtro de Período*) nativamente, não exigindo or loop.
'''

v_fuzz = '''# 3. Motor Heurístico: RapidFuzz (main.py)
A Busca Heurística ocorre quando a conciliação manual rápida é requisitada (Sienge vs Vulcano).

**Regras no Python:**
1. A biblioteca apidfuzz executa o modelo de distâncias matemáticas puras.
2. Utilizamos o **	oken_set_ratio**, que intercepta e retém as "palavras em comum" ignorando todo o lixo envolta de nomes (Ex: "João Silva da Cunha Me" vs "João Silva").

**Trecho Fonte da Matemática em main.py:**
`python
from rapidfuzz import fuzz

_score_nome = fuzz.token_set_ratio(c_nome, txt_clean)
_score_vl = 100 if abs(v_raiz - r_val) < 1.0 or abs(t_pago - r_val) < 1.0 else 0

_score_geral = (_score_nome * 0.4) + (_score_vl * 0.6)

is_diamante_c = _score_geral >= 85

# Se os dois são diamantes, consideraremos Match absoluto.
if is_diamante_c:
    candidatas.append({
       "score": int(_score_geral),
       "is_diamante": True
    })
`
'''

v_splink = '''# 4. Motor Probabilístico: Splink / DuckDB (poc_splink.py)
Invés do *RapidFuzz*, o **Splink** é disparado (pelos endpoints que setam use_splink = True da tela Smart Importer) para deduzir em ecossistemas de grande volume.

**Modelo Matemático Fellegi-Sunter no Backend:**
Ele não mede similaridade de String. Ele levanta a Tabela do Legacy Engine VENDAS (Vulcano) no DuckDBAPI em memória temporal:

`python
from splink import DuckDBAPI, Linker
import splink.comparison_library as cl

settings = {
    "link_type": "link_only",
    "comparisons": [
        cl.ExactMatch("num_parcela").configure(term_frequency_adjustments=True),
        cl.JaroWinklerAtThresholds("nome_comprador", [0.9, 0.8]),
        cl.AbsoluteDifferenceAtThresholds("valor_pago", [0.1, 1.0])
    ],
    "retain_matching_columns": True,
    "retain_intermediate_calculation_columns": True
}
`
*Detalhe das Regras:*
A predição "adivinha" ligações que perderam Unidade. Se o 
um_parcela cravar exato, mas o valor oscilar 1 real (AbsoluteDifference=1.0) devido à Mora, ele ainda apita como correlação confirmada, mesmo se o nome vier faturado no CNPJ do Cônjuge (m-probability).
'''

v_langgraph = '''# 5. A Orquestração LangGraph (Futura V2)
A Visão de Graph Routing no Backend para Agentes que não dependem da base do Smart Importer.

**Graph Schema Visual (Agentes):**
`python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(StateDict)
builder.add_node("Investigador", agente_investigador)
builder.add_node("Revisao_HITL", nodo_humano) 
builder.add_node("Autocorrecao", nodo_auto_correcao)

# Tool do Python consumida pelo Agente:
@tool
def analisar_estoque_lctoger(cc_empreendimento: int):
    \"\"\"Cruza o saldo base do centro de custo na 5639 para IFRS15.\"\"\"
    ...
`

**Como funciona:**
Se os orfãos sobrarem da esteira Splink/RapidFuzz, eles caem via Roteador Condicional para o Agente Investigador. Ele ativa ferramentas passivas contra o *Firebird* puramente para ver se a auditoria os escondeu ou se precisa alocar a baixa do Questor. Se alocado, pausa no Revisao_HITL e solicita um Clique no botão Vue (Human-In-The-Loop) para persistir o SQL INSERT.
'''

notes = {
    "1_Visao_Geral.md": v_geral,
    "2_Vertex_AI.md": v_vertex,
    "3_Pandas_Vetores.md": v_pandas,
    "4_RapidFuzz_Heuristica.md": v_fuzz,
    "5_Splink_DuckDB.md": v_splink,
    "6_LangGraph_Mentes.md": v_langgraph
}

for k, content in notes.items():
    with open(os.path.join(base_dir, k), "w", encoding="utf-8") as f:
        f.write(content)

print("Fragmentos enriquecidos atualizados!")
