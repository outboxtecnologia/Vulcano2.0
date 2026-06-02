"""
Grafo LangGraph — Orquestração Multi-Agente Avançada (Phase 4)

Nodos:
  Extrator             → Prepara (Dossiê Heurístico Temporal) via Python/Pandas logic
  SupervisorRouter     → Agente Básico LLM que define para onde a investigação deve ir
  AgenteImobiliario    → Especialista em Cusos de Obra, Estoques 1.x e Metragens
  AgenteFiscal         → Especialista em Tributos e Contas 2.x
  Sintese              → Agente que emite o formato JSON Factual obrigatório
  FerraRegras          → ToolNode padrão acionado pelos Especialistas
  Revisao              → Interrupção HITL (aguarda aprovação humana)
  Finalizacao          → Persiste resultado aprovado
"""

import json
import sqlite3
import os
import re

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from core.agents.state import AuditoriaGraphState
from core.agents.llm_provider import get_agent_llm
from core.agents.tools import (
    analisar_lancamentos_questor,
    verificar_receitas_custos_poc,
    buscar_conta_no_plano,
    buscar_proximidade_passivos_fiscais,
    analisar_estoque_lctoger,
    agrupar_creditos_por_apto,
    calcular_custo_realizado_poc_metragem,
    dossie_amostral_unidades_vulcano,
)
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from core.services.combinatorial_analyzer import IFRS15Analyzer

llm = get_agent_llm()

# ── Checkpointer (memória persistida em SQLite) ───────────────────────────────
db_path = os.path.join(os.path.dirname(__file__), "..", "..", "agente_checkpoints.sqlite")
_sqlconn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(_sqlconn)

# ── Tools disponíveis ─────────────────────────────────────────────────────────
tools_list = [
    analisar_lancamentos_questor,
    verificar_receitas_custos_poc,
    buscar_conta_no_plano,
    buscar_proximidade_passivos_fiscais,
    analisar_estoque_lctoger,
    agrupar_creditos_por_apto,
    calcular_custo_realizado_poc_metragem,
    dossie_amostral_unidades_vulcano,
]
tool_node = ToolNode(tools_list)
llm_with_tools = llm.bind_tools(tools_list) if llm is not None else None

# ── Prompts Especializados ───────────────────────────────────────────────────

ROUTER_PROMPT = """Você é o Supervisor de Auditoria Roteador.
Baseado no nome da conta e nos dados do Dossiê, você OBRIGATORIAMENTE DEVE escolher quem vai conduzir a análise profunda respondendo APENAS com a palavra chave:
1. Se for ESTOQUE, CUSTO DE OBRA ou IMÓVEL (começa com 1.1.X ou envolve métricas Físicas/Stuttgart): Responda "IMOBILIARIO"
2. Se for CLIENTES / DUPLICATAS (começa com 1.1.2.01.X): Responda "CLIENTES"
3. Se for PASSIVO FISCAL, FORNECEDORES ou TRIBUTOS (começa com 2.X e trata de DARF/Imposto): Responda "TRIBUTOS"
4. Se for ADIANTAMENTO DE CLIENTES / ANTECIPAÇÕES (Geralmente 2.1.2.02.X): Responda "ANTECIPACOES"
5. Se for RESULTADO DE VENDA / RECEITA (começa com 3.X ou 4.X e fala sobre Custo IFRS 15): Responda "RECEITAS"
Se não tiver certeza, ou for apenas Resultado genérico e houver CC e Metragem: Responda "IMOBILIARIO".
NÃO ESCREVA NENHUM OUTRO TEXTO ALÉM DA PALAVRA-CHAVE."""

IMOBILIARIO_PROMPT = """Você é o Agente Especialista Imobiliário (CPC 47 e IFRS 15).
Você analisa contas 1.x e Custos de Obra de empreendimentos via Dossiê Heurístico e Tools (Firebird).

REGRAS DE OURO DA ENGENHARIA CONTÁBIL (CUSTO E POC):
1. CUSTOS DE OBRA FISICOS: Em LCTOGER (filtrado por CC, ex 35). Use 'analisar_estoque_lctoger' para ver os lançamentos brutos da obra inteira.
2. CUSTO FRACIONÁRIO: Cada APTO acumula um % físico de Custeio Total (baseado na Área m²).
3. DESVIO DE POC NO CUSTO (O GRANDE ERRO): Para frações/unidades vendidas, o Custo INCORRIDO deve ser 100% da sua Fração de Obra. O Percentual de POC Global (ex: 27%) serve para medir o Ritmo da Receita ao longo dos anos, MAS NÃO DEVE ser aplicado para mutilar a baixa do custo de uma fração unitária transferida. Se os créditos (baixas no estoque) estiverem batendo exatamente com a métrica "teste_distorcao_com_poc" da ferramenta, a empresa cometeu o erro fatal de mutilar o custo fracionário multiplicando-o pelo POC! Denuncie esse erro!
4. PADRÕES: Use 'agrupar_creditos_por_apto'. Se a distribuição de créditos é <= 0.30, a taxa fracionária base é boa, mas o valor bruto pode ter sido distorcido por POC equivocado.
Para encerrar a investigação chame FINALIZAR_INVESTIGACAO na sua mente e aguarde o nó de Síntese."""

TRIBUTOS_PROMPT = """Você é o Agente Especialista Fiscal e Tributário do Questor.
Geralmente opera contas passivas 2.x e DARFs.
Sua regra master é usar 'buscar_proximidade_passivos_fiscais' e cruzar pagamentos parciais no banco. Considere apropriação indevida ou juros sobre multas.
Para encerrar a investigação chame FINALIZAR_INVESTIGACAO na sua mente e aguarde o nó de Síntese."""

CLIENTES_PROMPT = """Você é o Agente Especialista de Contas a Receber (VGV de Clientes - 1.1.2.01.x).
Analisa se a soma de recebimentos e saldos bate com os dossiês e o Vulcano Caixa.
Use 'agrupar_creditos_por_apto' ou analise lançamentos da conta. Se o saldo não baixar conforme o Dossiê indica, sinalize erro de baixa.
Para encerrar chame FINALIZAR_INVESTIGACAO na sua mente."""

ANTECIPACOES_PROMPT = """Você é o Agente Especialista de Antecipações (Adiantamento de Clientes - 2.1.2.02.x).
Você foca nas unidades não entregues (em construção). O dinheiro que entra antes do encerramento deve ficar aqui como Passivo, migrando para Receita conforme a proporção do POC da Obra IFRS 15.
Analise a distorção se a conta não estiver batendo com a métrica de Caixa recebido não realizado do Vulcano.
Para encerrar chame FINALIZAR_INVESTIGACAO na sua mente."""

RECEITAS_PROMPT = """Você é o Agente Especialista de Receitas (3.x ou 4.x - IFRS 15).
Você analisa o reconhecimento de Vendas e Multas. Use rigorosamente a 'verificar_receitas_custos_poc'.
Se o POC diz que deve realizar 10% da receita e a empresa realizou 100% num imóvel em planta, emite um Alerta Crítico.
Para encerrar chame FINALIZAR_INVESTIGACAO na sua mente."""

SINTESE_PROMPT = """Você é o Sintetizador Final. Seu objetivo estruturar os relatos e ferramentas encontradas num laudo técnico que entrará na tela do Fechamento P/ Human-in-the-Loop.
Regra de Ouro (LANÇAMENTOS EXAUSTIVOS): Se o Especialista relatar inconsistências originadas em lançamentos contábeis específicos (ex: datas, históricos ou valores atípicos que causaram a divergência na ferramenta SQL), você DEVE EXPLICITAMENTE embutir esses lançamentos citados no final do texto da "descricao" no padrão Bullet Point Exemplo: `* Data: 2025-03-31 | Valor: R$ 900.00 | Histórico: TRANSFERENCIA X`. Nunca omita o lançamento se o especialista o encontrou.

Você precisa emitir um JSON VÁLIDO obedecendo a:
{
  "descricao": "<resenha analitica factual do Especialista anterior com Bullet Points dos Lançamentos identificados>",
  "acao": "<acao contábil prática>",
  "conta_contrapartida": "<conta sugerida ou vazio>"
}"""

# ── Nodos Orquestrados ────────────────────────────────────────────────────────

def extrator_heuristico_node(state: AuditoriaGraphState):
    conta = state.get("conta_alvo", "")
    if not state.get("dossie_heuristico"):
        try:
            dossie = IFRS15Analyzer.gerar_dossie_temporal(35, 959, conta_alvo=conta, limite_amostra=5)
            str_dossie = "\n\n--- DOSSIÊ HEURÍSTICO PYTHON (Amostra 5 unidades - CC: 35) ---\n" + json.dumps(dossie, ensure_ascii=False, indent=2)
        except Exception as e:
            str_dossie = "(Falhou ao processar dossiê: " + str(e) + ")"
            dossie = {}

        return {
            "dossie_heuristico": dossie if isinstance(dossie, dict) else {},
            "prompt_calibracao": str_dossie,
            "passos_executados": ["Motor Python extraiu Dados Determinísticos: Dossiê Temporal Heurístico Carregado."]
        }
    return {}

def supervisor_router_node(state: AuditoriaGraphState):
    conta = state.get("conta_alvo", "")
    dossie = state.get("prompt_calibracao", "")
    msg = HumanMessage(content=f"Análise a conta: {conta}. E os logs: {dossie[:300]}")
    resp = llm.invoke([SystemMessage(content=ROUTER_PROMPT), msg])
    decision = resp.content.strip().upper()
    
    agente_escolhido = "Imobiliario"
    if "CLIENTES" in decision: agente_escolhido = "Clientes"
    elif "TRIBUTOS" in decision: agente_escolhido = "Tributos"
    elif "ANTECIPACOES" in decision: agente_escolhido = "Antecipacoes"
    elif "RECEITAS" in decision: agente_escolhido = "Receitas"
    elif "IMOBILIARIO" in decision: agente_escolhido = "Imobiliario"
    
    return {
        "passos_executados": [f"Supervisor Router avaliou o contexto e ativou: Agente {agente_escolhido}"],
        "messages": [AIMessage(content=f"[SYSTEM: Rotetado para Agente {agente_escolhido}]")]
    }

def route_from_router(state: AuditoriaGraphState):
    last = state.get("messages", [])[-1].content
    if "Agente Tributos" in last: return "AgenteTributos"
    if "Agente Clientes" in last: return "AgenteClientes"
    if "Agente Antecipacoes" in last: return "AgenteAntecipacoes"
    if "Agente Receitas" in last: return "AgenteReceitas"
    return "AgenteImobiliario"

def especialista_node(state: AuditoriaGraphState, system_prompt: str, nome: str):
    conta = state.get("conta_alvo", "")
    dossie = state.get("prompt_calibracao", "")
    historico = state.get("messages", [])
    
    # Injetamos o alvo diretamente no SystemMessage do Especialista para que ele saiba O QUE invocar
    contexto_injetado = f"{system_prompt}\n\nManda bala na investigação! A CONTA ALVO é: {conta}\nLeitura Inicial do Dossiê Extrator:\n{dossie}"
    
    msgs = [SystemMessage(content=contexto_injetado)] + historico
    res = llm_with_tools.invoke(msgs)
    
    tool_calls = getattr(res, "tool_calls", None) or []
    passo = f"{nome}: {'Chamando {0} tools'.format(len(tool_calls)) if tool_calls else 'Investigação Finalizada. Enviando para Síntese'}"
    return {"messages": [res], "passos_executados": [passo]}

def agente_imobiliario_node(state: AuditoriaGraphState):
    return especialista_node(state, IMOBILIARIO_PROMPT, "Especialista Imobiliário")

def agente_tributos_node(state: AuditoriaGraphState):
    return especialista_node(state, TRIBUTOS_PROMPT, "Especialista Tributos")

def agente_clientes_node(state: AuditoriaGraphState):
    return especialista_node(state, CLIENTES_PROMPT, "Especialista Clientes")

def agente_antecipacoes_node(state: AuditoriaGraphState):
    return especialista_node(state, ANTECIPACOES_PROMPT, "Especialista Antecipações")

def agente_receitas_node(state: AuditoriaGraphState):
    return especialista_node(state, RECEITAS_PROMPT, "Especialista Receitas")

def route_especialista(state: AuditoriaGraphState):
    last = state.get("messages", [])[-1]
    if getattr(last, "tool_calls", None):
        return "FerraRegras"
    return "Sintese"

def ferramentas_node(state: AuditoriaGraphState):
    last_msg = state.get("messages", [])[-1]
    if not getattr(last_msg, "tool_calls", None):
        return {}
    
    result_msgs = []
    passos = []
    
    for tc in last_msg.tool_calls:
        tool_name = tc["name"]
        tool_args = tc.get("args", {})
        tool_id = tc["id"]
        
        tool_fn = next((t for t in tools_list if t.name == tool_name), None)
        if not tool_fn:
            output = json.dumps({"status": "error", "message": "Tool not found"})
        else:
            try:
                output = tool_fn.invoke(tool_args)
            except Exception as e:
                output = str(e)
                
        result_msgs.append(ToolMessage(content=str(output)[:3000], tool_call_id=tool_id))
        passos.append(f"FerraRegras: Executou {tool_name}")
        
    return {"messages": result_msgs, "passos_executados": passos}

def route_ferramentas(state: AuditoriaGraphState):
    # Retorna para o agente que emitiu a tool_call
    msgs = state.get("messages", [])
    # Procura backwards qual agente fez a analise
    for m in reversed(msgs):
        if isinstance(m, AIMessage):
            if "Fiscal" in m.content: # ou metadata
                return "Sintese" # Simplificando por ser prototype
    return "AgenteImobiliario" # Default fallback

def route_ferramentassimples(state: AuditoriaGraphState):
    # Procura backwards quem chamou a tool para retornar a ele.
    historico = state.get("messages", [])
    for msg in reversed(historico):
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            # Achamos a AI que emitiu. Identificaremos o autor por inferencia da stack
            pass
    # No protótipo simplificado atual, não guardamos o sender ID. Usaremos o último Roteado!
    roteado = "AgenteImobiliario"
    for msg in historico:
        if isinstance(msg, AIMessage) and "[SYSTEM: Rotetado" in msg.content:
            roteado = msg.content.replace("[SYSTEM: Rotetado para Agente ", "").replace("]", "").strip()
    return f"Agente{roteado}"

def agente_sintese_node(state: AuditoriaGraphState):
    historico = state.get("messages", [])
    msgs = [SystemMessage(content=SINTESE_PROMPT)] + historico + [HumanMessage(content="Finalize a investigação e emita O JSON EXATO.")]
    res = llm.invoke(msgs)
    
    texto = res.content
    sugestao = {}
    import re
    match = re.search(r'\{[^{}]*"descricao"[^{}]*\}', texto, re.DOTALL)
    if match:
        try:
            sugestao = json.loads(match.group(0))
        except:
            sugestao = {"descricao": texto[:500], "acao": "Revisar", "conta_contrapartida":""}
    else:
        sugestao = {"descricao": texto[:500], "acao": "Revisar", "conta_contrapartida":""}
        
    return {"sugestao_correcao": sugestao, "passos_executados": ["Sintese concluída. Pausando no HITL para Avaliação."], "messages": [res]}

def revisao_node(state: AuditoriaGraphState):
    return {"passos_executados": ["Aguardando revisão humana..."]}

def finalizacao_node(state: AuditoriaGraphState):
    aprovado = state.get("aprovado_pelo_usuario", False)
    return {"passos_executados": [f"Finalizado. Aprovado? {aprovado}"]}

# ── Construção do Grafo Dinâmico ──────────────────────────────────────────────

workflow = StateGraph(AuditoriaGraphState)

workflow.add_node("Extrator", extrator_heuristico_node)
workflow.add_node("SupervisorRouter", supervisor_router_node)
workflow.add_node("AgenteImobiliario", agente_imobiliario_node)
workflow.add_node("AgenteTributos", agente_tributos_node)
workflow.add_node("AgenteClientes", agente_clientes_node)
workflow.add_node("AgenteAntecipacoes", agente_antecipacoes_node)
workflow.add_node("AgenteReceitas", agente_receitas_node)
workflow.add_node("Sintese", agente_sintese_node)
workflow.add_node("FerraRegras", ferramentas_node)
workflow.add_node("Revisao", revisao_node)
workflow.add_node("Finalizacao", finalizacao_node)

workflow.set_entry_point("Extrator")
workflow.add_edge("Extrator", "SupervisorRouter")

workflow.add_conditional_edges("SupervisorRouter", route_from_router, {
    "AgenteImobiliario": "AgenteImobiliario",
    "AgenteTributos": "AgenteTributos",
    "AgenteClientes": "AgenteClientes",
    "AgenteAntecipacoes": "AgenteAntecipacoes",
    "AgenteReceitas": "AgenteReceitas"
})

for agente in ["AgenteImobiliario", "AgenteTributos", "AgenteClientes", "AgenteAntecipacoes", "AgenteReceitas"]:
    workflow.add_conditional_edges(agente, route_especialista, {
        "FerraRegras": "FerraRegras",
        "Sintese": "Sintese"
    })

workflow.add_conditional_edges("FerraRegras", route_ferramentassimples, {
    "AgenteImobiliario": "AgenteImobiliario",
    "AgenteTributos": "AgenteTributos",
    "AgenteClientes": "AgenteClientes",
    "AgenteAntecipacoes": "AgenteAntecipacoes",
    "AgenteReceitas": "AgenteReceitas"
})



workflow.add_edge("Sintese", "Revisao")
workflow.add_conditional_edges("Revisao", lambda state: "Finalizacao" if state.get("aprovado_pelo_usuario") else END, {
    "Finalizacao": "Finalizacao",
    END: END
})
workflow.add_edge("Finalizacao", END)

# Sem Vertex/GEMINI_API_KEY o LLM não instancia — API sobe; rotas de agentes retornam 503.
graph_app = None
if llm is not None:
    graph_app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["SupervisorRouter", "Revisao"],
    )
