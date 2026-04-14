"""
Grafo LangGraph — Agente Investigativo de Auditoria Contábil (ReAct)

Nodos:
  Supervisor   → LLM com tool-calling ReAct
  FerraRegras  → ToolNode (executa tools reais no Firebird/SQLite)
  Revisao      → Interrupção HITL (aguarda aprovação humana)
  Finalizacao  → Persiste resultado aprovado

Fluxo:
  Supervisor ──(tool_call)──→ FerraRegras ──→ Supervisor (loop ReAct)
  Supervisor ──(resposta)──→ Revisao (PAUSE)
  Revisao ──(aprovado=True)──→ Finalizacao
  Revisao ──(aprovado=False)──→ END
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from core.agents.state import AuditoriaGraphState
from core.agents.llm_provider import get_agent_llm
from core.agents.tools import (
    analisar_lancamentos_questor,
    verificar_receitas_custos_poc,
    buscar_conta_no_plano,
    buscar_proximidade_passivos_fiscais,
)
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
import json
import sqlite3
import os

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
]
tool_node = ToolNode(tools_list)

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Você é um Agente Investigativo Contábil especializado em reconciliar divergências no ERP Questor.
Você tem acesso a ferramentas SQL que consultam o banco Firebird (Questor/Vulcano) e o SQLite (poc_database).

Missão:
1. Receba a conta alvo e chame OBRIGATORIAMENTE pelo menos 2 ferramentas para coletar dados reais.
2. A ferramenta `buscar_conta_no_plano` deve ser a primeira chamada para entender o grupo da conta.
3. Use `analisar_lancamentos_questor` para ver o histórico físico de lançamentos.
4. Se for conta de resultado/receita, use `verificar_receitas_custos_poc`.
5. Se for passivo ou tributo, use `buscar_proximidade_passivos_fiscais`.
6. Após coletar os dados, formule uma sugestão de correção concreta baseada nos fatos reais encontrados.

Regras IFRS 15 / CPC 47:
- Receita é reconhecida com base na POC (Percentual de Obra Concluída) × VGV por venda individual.
- Custos são reconhecidos proporcionalmente à fração de área de cada unidade.
- Divergências comuns: diferença de timing, conta filho vs conta mãe, lançamento ZZ zerado.

Formato da sugestão final (após ferramentas):
Responda em JSON com:
{
  "descricao": "<análise factual baseada nos dados retornados pelas ferramentas>",
  "acao": "<ação contábil recomendada: ex: Reclassificar, Estornar, Complementar, Verificar lançamento X>",
  "conta_contrapartida": "<conta sugerida para a contrapartida, ex: 5.1.02.001>"
}
"""

# ── Nodo Supervisor (ReAct Loop) ───────────────────────────────────────────────
def supervisor_node(state: AuditoriaGraphState):
    llm = get_agent_llm().bind_tools(tools_list)
    conta = state.get("conta_alvo", "conta desconhecida")

    # Monta o histórico de mensagens acumulado
    historico_msgs = state.get("messages", [])

    if not historico_msgs:
        # Primeira chamada: inicializa
        msgs = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Investigue a divergência na conta: {conta}. Comece coletando dados com as ferramentas disponíveis.")
        ]
    else:
        msgs = [SystemMessage(content=SYSTEM_PROMPT)] + historico_msgs

    res = llm.invoke(msgs)

    # Determina se o LLM quer chamar tools ou finalizou
    tool_calls = getattr(res, "tool_calls", None) or []

    passo = f"Supervisor: {'Chamando ' + ', '.join(tc['name'] for tc in tool_calls) if tool_calls else 'Formulando resposta final'}"

    novo_state = {
        "passos_executados": [passo],
        "messages": (historico_msgs or []) + [res],
    }

    # Se o LLM respondeu com texto final (sem mais tool calls), extrai a sugestão
    if not tool_calls:
        texto = ""
        if hasattr(res, "content"):
            c = res.content
            if isinstance(c, list):
                for part in c:
                    if isinstance(part, dict) and part.get("type") == "text":
                        texto += part.get("text", "")
            else:
                texto = str(c)

        # Tenta extrair JSON da resposta
        sugestao = _extract_json_sugestao(texto, conta)
        novo_state["sugestao_correcao"] = sugestao

    return novo_state


def _extract_json_sugestao(texto: str, conta_alvo: str) -> dict:
    """Extrai o JSON de sugestão do texto do LLM. Fallback gracioso se não encontrar."""
    import re
    # Tenta encontrar bloco JSON na resposta
    match = re.search(r'\{[^{}]*"descricao"[^{}]*\}', texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    # Fallback: usa o texto como descrição
    descricao = texto.strip()[:500] if texto.strip() else f"Análise da conta {conta_alvo} concluída."
    return {
        "descricao": descricao,
        "acao": "Revisar manualmente os lançamentos identificados nas ferramentas",
        "conta_contrapartida": "—"
    }


# ── Nodo de Ferramentas (ToolNode padrão LangGraph) ───────────────────────────
def ferramentas_node(state: AuditoriaGraphState):
    """Executa as tools solicitadas pelo LLM e adiciona os resultados ao histórico."""
    historico = state.get("messages", [])
    last_msg = historico[-1] if historico else None

    if not last_msg or not getattr(last_msg, "tool_calls", None):
        return {"passos_executados": ["Ferramenta: nenhuma tool_call encontrada"]}

    # Usa o ToolNode do LangGraph para executar
    result_msgs = []
    resultados_db = list(state.get("resultados_db", []))
    passos = []

    for tc in last_msg.tool_calls:
        tool_name = tc["name"]
        tool_args = tc["args"]
        tool_id   = tc["id"]

        # Localiza a ferramenta pelo nome
        tool_fn = next((t for t in tools_list if t.name == tool_name), None)
        if tool_fn is None:
            output = json.dumps({"status": "error", "message": f"Tool {tool_name} não encontrada"})
        else:
            try:
                output = tool_fn.invoke(tool_args)
            except Exception as e:
                output = json.dumps({"status": "error", "message": str(e)})

        result_msgs.append(ToolMessage(content=str(output), tool_call_id=tool_id))
        resultados_db.append({"tool": tool_name, "args": tool_args, "result": output})
        passos.append(f"Tool '{tool_name}' executada → {len(str(output))} chars de resultado")

    return {
        "messages": historico + result_msgs,
        "resultados_db": resultados_db,
        "passos_executados": passos,
    }


# ── Nodo de Revisão HITL ──────────────────────────────────────────────────────
def revisao_node(state: AuditoriaGraphState):
    """Ponto de interrupção HITL. O grafo pausa aqui para aguardar aprovação humana."""
    return {"passos_executados": ["Aguardando revisão humana (HITL interrupt)..."]}


# ── Nodo de Finalização ───────────────────────────────────────────────────────
def finalizacao_node(state: AuditoriaGraphState):
    """Executado após aprovação humana. Persiste o resultado e encerra."""
    aprovado = state.get("aprovado_pelo_usuario", False)
    feedback = state.get("feedback_usuario", "")
    sugestao = state.get("sugestao_correcao", {})

    passo = (
        f"Correção APROVADA pelo usuário. Feedback: '{feedback}'. Ação: {sugestao.get('acao', '—')}"
        if aprovado
        else f"Correção REJEITADA pelo usuário. Feedback: '{feedback}'. Ciclo encerrado sem alteração."
    )
    return {"passos_executados": [passo]}


# ── Roteamento condicional do Supervisor ────────────────────────────────────
def _route_supervisor(state: AuditoriaGraphState):
    """Se o LLM ainda quer chamar tools, vai para FerraRegras. Senão, vai para Revisao."""
    msgs = state.get("messages", [])
    last = msgs[-1] if msgs else None
    if last and getattr(last, "tool_calls", None):
        return "FerraRegras"
    return "Revisao"


def _route_revisao(state: AuditoriaGraphState):
    """Após HITL: aprovado → Finalização; rejeitado → END."""
    if state.get("aprovado_pelo_usuario", False):
        return "Finalizacao"
    return END


# ── Construção do Grafo ───────────────────────────────────────────────────────
workflow = StateGraph(AuditoriaGraphState)

workflow.add_node("Supervisor",   supervisor_node)
workflow.add_node("FerraRegras",  ferramentas_node)
workflow.add_node("Revisao",      revisao_node)
workflow.add_node("Finalizacao",  finalizacao_node)

workflow.set_entry_point("Supervisor")

workflow.add_conditional_edges("Supervisor", _route_supervisor, {
    "FerraRegras": "FerraRegras",
    "Revisao":     "Revisao",
})
workflow.add_edge("FerraRegras", "Supervisor")   # Loop ReAct
workflow.add_conditional_edges("Revisao", _route_revisao, {
    "Finalizacao": "Finalizacao",
    END:           END,
})
workflow.add_edge("Finalizacao", END)

# Compila com checkpointer e pausa HITL antes de Revisao
graph_app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["Revisao"]
)
