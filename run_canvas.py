import os
import json

base_dir = r"docs\MOCs\Deep_Dives\Fluxo_Auditoria"
os.makedirs(base_dir, exist_ok=True)

v_geral = '''# O Fluxo de Auditoria e Conciliação
Este é o coração do sistema Smart Importer + Auditoria ERP.
Ele converte "caos humano" (relatórios em PDF, nomes digitados errados, dados bancários paralelos) em verdade matemática na conta de Caixa e Receita (4910 e 230) do Questor.

Siga a trilha pelo Canvas para ver o comportamento de cada tecnologia sob o capô.
'''

v_vertex = '''# 1. Prompt Vertex AI e Extração
A IA Generativa (gemini-2.5-flash) é usada unicamente como "Transcritor Semântico de OCR". Ela não faz matemática aqui.

**O Prompt Interno:**
O backend isola o PDF e injeta nesta f-string restritiva:
`json
SCHEMA EXIGIDO GERAÇÃO:
{
  "registros": [
    {
      "comprador": "Nome",
      "cpf_cnpj": "Apenas Numeros",
      "dt_vencimento": "DD/MM/YYYY",
      "total_pago": 0.00
    }
  ]
}
`

**Condições Especiais:**
- 	hinking_budget: 0: Força a IA a cuspir o JSON nativo sem gastar tempo ou tokens explicando raciocínio (Chain of Thought).
- Tempo de resposta cai de 25s para 3s nas páginas de relatório.
'''

v_pandas = '''# 2. Vetorização com Pandas
O JSON retornado da IA iterado num laço or simples derrubaria o servidor FastAPI na hora de fazer casting de data e lidar com nulos. 

**O Papel do Pandas:**
- Transforma as centenas de dicionários soltos em um DataFrame.
- **Casting Rápido Data/Tempo:** df['DATA_ISO'] = pd.to_datetime(df['DATA']).dt.strftime('%Y-%m-%d'). 
- Isso permite que você possa filtrar na UI a "Data Final e Inicial" instantaneamente, resolvendo anomalias de String.
- **Higienização Serial:** .replace({np.nan: None}) converte buracos do Dataframe Pandas em um 
ull puro de JSON para o Vue/React não engasgo ou dar "undefined".
'''

v_fuzz = '''# 3. Motor Heurístico: RapidFuzz
Se o usuário **não ativar** a predição avançada (use_splink=False), o sistema usa uma força-bruta matemática para pareamento em memória.

**A Biblioteca RapidFuzz:**
Compara o "Nome do Cliente no PDF" com "Nome do Vulcano" usando:
- uzz.token_set_ratio: Ignore a ordem e as palavras sobrando!
  *Ex: "JOAO SILVA" vs "JOAO DA SILVA E CIA" -> Score 100*.
- Se o score de nome e o valor cravarem mais de **85%**, a Engine coroa a baixa como **is_diamante: True**, o que significa perfeição para a Auditoria.
'''

v_splink = '''# 4. Motor Probabilístico: Splink (DuckDB)
Para bases imensas e caóticas com muitos distratos e trocas de titularidade.

**Como funciona (Fellegi-Sunter):**
Não compara "apenas se as strings se parecem". Ele calcula em background:
1. Qual a chance do CPF bater com esse nome (m-probability).
2. Mas espera... Tem muitos "Josés" no Vulcano (u-probability). 
3. Ele constrói um modelo vetorial preditivo suportado pelo banco *DuckDB* em milissegundos e retorna: *"Probabilidade 99.8% de que são o mesmo contrato"*.
'''

v_langgraph = '''# 5. A Orquestração LangGraph (Futura V2)
Como está o esquema desenhado e montado em testes para os Multi-Agentes!

O LangGraph não lida com o PDF, ele assume que o erro é insolúvel pelos motores anteriores.

**Estados do Grafo:**
1. **Nó de Ferramentas (Investigador):** Recebe o "Órfão" (sem match). Avalia o Toolkit: nalisar_estoque_lctoger (pesquisa LCTOGER pelo CC) e nalisar_lancamentos_questor (busca contas no plano). 
2. **Nó de Autocorreção:** Se o SQL quebrou ou trouxe nulo, ele não falha a API. O Grafo refaz o prompt por si mesmo (ciclo reflexivo) dizendo "Sua query deu KeyError, refaça".
3. **Nó Human-in-the-Loop (Revisão):** Bateu na trava de decisão (suspensão). Aparecerá um Modal no Frontend para o Contador revisar a proposta do robô.
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

canvas_data = {
  "nodes": [
    {"id": "n1", "type": "file", "file": r"docs\MOCs\Deep_Dives\Fluxo_Auditoria\1_Visao_Geral.md", "x": -500, "y": -150, "width": 400, "height": 300, "color": "4"},
    {"id": "n2", "type": "file", "file": r"docs\MOCs\Deep_Dives\Fluxo_Auditoria\2_Vertex_AI.md", "x": 0, "y": -150, "width": 400, "height": 450, "color": "1"},
    {"id": "n3", "type": "file", "file": r"docs\MOCs\Deep_Dives\Fluxo_Auditoria\3_Pandas_Vetores.md", "x": 500, "y": -150, "width": 400, "height": 400, "color": "2"},
    {"id": "n4", "type": "file", "file": r"docs\MOCs\Deep_Dives\Fluxo_Auditoria\4_RapidFuzz_Heuristica.md", "x": 1000, "y": -400, "width": 400, "height": 350, "color": "6"},
    {"id": "n5", "type": "file", "file": r"docs\MOCs\Deep_Dives\Fluxo_Auditoria\5_Splink_DuckDB.md", "x": 1000, "y": 100, "width": 400, "height": 350, "color": "6"},
    {"id": "n6", "type": "file", "file": r"docs\MOCs\Deep_Dives\Fluxo_Auditoria\6_LangGraph_Mentes.md", "x": 1500, "y": -150, "width": 400, "height": 450, "color": "3"},
    
    {"id": "t1", "type": "text", "text": "## Recebimento Auditado ✅\nLançado no Vulcano via SQLite/Firebird e reflete puramente as Colunas Comparativas no ERP Auditoria (4910 vs 230).", "x": 1500, "y": 400, "width": 400, "height": 200, "color": "5"}
  ],
  "edges": [
    {"id": "e1", "fromNode": "n1", "fromSide": "right", "toNode": "n2", "toSide": "left"},
    {"id": "e2", "fromNode": "n2", "fromSide": "right", "toNode": "n3", "toSide": "left"},
    {"id": "e3", "fromNode": "n3", "fromSide": "right", "toNode": "n4", "toSide": "left"},
    {"id": "e4", "fromNode": "n3", "fromSide": "right", "toNode": "n5", "toSide": "left"},
    {"id": "e5", "fromNode": "n4", "fromSide": "right", "toNode": "n6", "toSide": "left", "label": "No Match (Órfão)"},
    {"id": "e6", "fromNode": "n5", "fromSide": "right", "toNode": "n6", "toSide": "left", "label": "No Match (Órfão)"},
    {"id": "e7", "fromNode": "n4", "fromSide": "right", "toNode": "t1", "toSide": "top", "label": "Match Diamante"},
    {"id": "e8", "fromNode": "n5", "fromSide": "right", "toNode": "t1", "toSide": "left", "label": "Prob > 99.8%"}
  ]
}

with open(r"docs\MOCs\Deep_Dives\Lousa_Fluxo_Auditoria_Arquitetura.canvas", "w", encoding="utf-8") as f:
    json.dump(canvas_data, f, indent=2, ensure_ascii=False)
