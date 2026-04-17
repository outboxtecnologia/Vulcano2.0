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
    analisar_estoque_lctoger,
    agrupar_creditos_por_apto,
    calcular_custo_realizado_poc_metragem,
    dossie_amostral_unidades_vulcano,
)
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
import json
import sqlite3
import os
from core.services.combinatorial_analyzer import IFRS15Analyzer

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

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Você é um Agente Investigativo Contábil especializado em reconciliar divergências no ERP Questor.
Você tem acesso a ferramentas SQL que consultam o banco Firebird (Questor/Vulcano) e o SQLite (poc_database).

Missão:
1. Receba a conta alvo e chame OBRIGATORIAMENTE pelo menos 2 ferramentas para coletar dados reais.
2. A ferramenta `buscar_conta_no_plano` deve ser a primeira chamada para entender o grupo da conta.
3. Use `analisar_lancamentos_questor` para ver o histórico físico de lançamentos (amostra rápida).
4. Se for conta de resultado/receita (classif 4.x ou 5.x), use `verificar_receitas_custos_poc`.
5. Se for passivo ou tributo (classif 2.x), use `buscar_proximidade_passivos_fiscais`.

REGRAS ESPECIAIS para contas de ESTOQUE DE OBRA (classif 1.x — ex: IMÓVEIS A CONCLUIR):
6. PADRÃO DE OBRA: nos empreendimentos imobiliários em construção, os gastos de obra são
   lançados DIRETAMENTE em LCTOGER pelo Centro de Custo (CC) do empreendimento,
   INDEPENDENTEMENTE da conta contábil. O CC é o identificador-chave do empreendimento.
   Exemplo: Res. Stuttgart = CC 35.
   NUNCA filtre por conta ao analisar LCTOGER para contas 1.x. Filtre sempre por CC.
7. Chame OBRIGATORIAMENTE `analisar_estoque_lctoger` com o parâmetro `cc_empreendimento`:
   - Isto ativa o modo CC que retorna TODOS os lançamentos do empreendimento no LCTOGER.
   - Exemplo: analisar_estoque_lctoger(conta_alvo='5639', cc_empreendimento=35)
   - O retorno inclui `contas_mais_debitadas_no_cc` (top-15) para mapear a composição de custo.
   - `conta_alvo_presente_nos_lancamentos` = True confirma que a conta 1.x aparece neste CC.
   - Se False: conta ou CC incorretos, ou não há lançamentos no período consultado.
8. Se a conta tem créditos com APTO no histórico, chame `agrupar_creditos_por_apto`:
   - `coeficiente_variacao` < 0.30 = distribuição UNIFORME (fração física provavelmente correta)
   - `coeficiente_variacao` > 0.60 = distribuição CONCENTRADA (investigar unidades de valor atípico)
   - O % de cada APTO deve ser proporcional à sua fração de área sobre a área total do empreendimento.
   - Um crédito em conta 1.x não representa fluxo financeiro mas estimativa de custo incorrido.
9. OBRIGATÓRIO: Para testar a exatidão fracionária do Estoque, chame calcular_custo_realizado_poc_metragem(cc_empreendimento). Se a unidade bater perfeitamente com a rubrica 	este_distorcao_com_poc em vez de custo_correto_ifrs15, AONDE HOUVER erro, a recomendação (acao) é refazer o custeio: a empresa aplicou o % de POC sobre a mensuração do custo inadvertidamente.

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

def extrator_heuristico_node(state: AuditoriaGraphState):
    """
    Roda apenas uma vez no inicio do Grafo: Extrai os dados do Firebird/SQLite,
    monta a matriz temporal (Dossiê) e formata o prompt de calibração para o HITL.
    """
    conta = state.get("conta_alvo", "")
    active_system_prompt = state.get("prompt_calibracao") or SYSTEM_PROMPT
    
    if not state.get("dossie_heuristico"):
        try:
            dossie = IFRS15Analyzer.gerar_dossie_temporal(35, 959, conta_alvo=conta, limite_amostra=5)
            str_dossie = "\\n\\n--- DOSSIÊ HEURÍSTICO PYTHON (Amostra 5 unidades - CC: 35) ---\\n" + json.dumps(dossie, ensure_ascii=False, indent=2)
        except Exception as e:
            str_dossie = "\\n\\n(Falhou ao processar dossiê heurístico: " + str(e) + ")"
            dossie = {}

        prompt_com_amostra = active_system_prompt + "\\n\\nConta alvo: " + conta + str_dossie
        _dossie_val = dossie if isinstance(dossie, dict) else {}
        
        return {
            "prompt_calibracao": prompt_com_amostra, 
            "dossie_heuristico": _dossie_val, 
            "passos_executados": ["Pausado para Calibração Visual do Dossiê. Verifique a nova tabela abaixo."]
        }
    return {}

def supervisor_node(state: AuditoriaGraphState):
    """
    Nó LLM: Invoca o Vertex AI com base no Prompt de Calibração (que pode ter sido reescrito pelo usuário).
    """
    conta = state.get("conta_alvo", "")
    hist = state.get("historico_aprendizado", [])
    
    # O user pode ter reescrito o prompt_calibracao na tela de pause:
    final_prompt = state.get("prompt_calibracao") or SYSTEM_PROMPT
    
    messages = [SystemMessage(content=final_prompt)]
    historico_msgs = state.get("messages", [])
    # Rehidrata MSGS antigas se precisar (simplificado)
    messages.extend(historico_msgs)
    
    if state.get("sugestao_correcao"):
        messages.append(HumanMessage(content=f"Dica p/ autocorreção: {json.dumps(state['sugestao_correcao'])}"))
        
    print("[Supervisor] Chamando Vertex AI...")
    response = llm.invoke(messages)
    
    return {"messages": [response], "passos_executados": ["Supervisor (LLM) avaliou os dados e tomou decisão."]}

# Monta as mensagens para enviar ao LLM
    # IMPORTANTE: o LangGraph acumula via operator.add — não re-passamos o historico no retorno
    historico_msgs = state.get("messages", [])

    if not historico_msgs:
        # Primeira chamada: cria a mensagem humana inicial e envia junto
        user_msg = HumanMessage(content=f"Investigue a divergência na conta: {conta}. Comece coletando dados com as ferramentas disponíveis.")
        msgs = [SystemMessage(content=SYSTEM_PROMPT), user_msg]
        # Retorna a HumanMessage inicial para o estado (delta)
        msgs_delta_pre = [user_msg]
    else:
        msgs = [SystemMessage(content=SYSTEM_PROMPT)] + historico_msgs
        msgs_delta_pre = []

    res = llm.invoke(msgs)

    # Determina se o LLM quer chamar tools ou finalizou
    tool_calls = getattr(res, "tool_calls", None) or []

    passo = f"Supervisor: {'Chamando ' + ', '.join(tc['name'] for tc in tool_calls) if tool_calls else 'Formulando resposta final'}"

    # Retorna APENAS as novas mensagens (delta) — operator.add faz a concatenação
    novo_state = {
        "passos_executados": [passo],
        "messages": msgs_delta_pre + [res],
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

    # Executa todas as tools e coleta apenas as ToolMessages (delta)
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

    # Retorna APENAS as novas ToolMessages (delta) — operator.add faz a concatenação
    return {
        "messages": result_msgs,
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


# ── Nodo de Autocorreção Reflexiva (Tarefa 3 do Roadmap) ──────────────────────
MAX_AUTOCORRECOES = 2  # Máximo de tentativas antes de desistir e ir para Revisao

def autocorrecao_node(state: AuditoriaGraphState):
    """Detecta erros nas ToolMessages, classifica a causa e injeta uma mensagem
    corretiva no loop ReAct para que o LLM tente novamente com parâmetros ajustados.
    Limita a MAX_AUTOCORRECOES ciclos para evitar loop infinito."""

    msgs = state.get("messages", [])
    tentativas = state.get("tentativas_autocorrecao", 0)

    # Coleta ToolMessages com erro na última rodada de ferramentas
    # Procura do fim do histórico até a última AIMessage (que continha os tool_calls)
    erros_encontrados = []
    for msg in reversed(msgs):
        from langchain_core.messages import ToolMessage, AIMessage
        if isinstance(msg, AIMessage):
            break  # Parou na AIMessage da rodada — saímos do loop
        if isinstance(msg, ToolMessage):
            try:
                parsed = json.loads(msg.content)
                if parsed.get("status") == "error":
                    erros_encontrados.append(parsed.get("message", "erro desconhecido"))
            except Exception:
                # Conteúdo não é JSON — verifica texto livre
                if "error" in msg.content.lower() or "traceback" in msg.content.lower():
                    erros_encontrados.append(msg.content[:200])

    # Classifica o tipo de erro e monta instrução de correção
    instrucao_correcao = ""
    for erro in erros_encontrados:
        err_lower = erro.lower()
        if "não encontrei número de conta" in err_lower or "número de conta não encontrado" in err_lower:
            instrucao_correcao += (
                "ERRO DE PARÂMETRO: o argumento `conta_alvo` deve conter apenas o número da conta (ex: '5639'). "
                "Não inclua palavras como 'conta', 'classif', ou o nome da conta. Use apenas os dígitos.\n"
            )
        elif "connection" in err_lower or "firebird" in err_lower or "unavailable" in err_lower:
            instrucao_correcao += (
                "ERRO DE CONEXÃO: o banco Firebird está inacessível. "
                "Tente novamente com a mesma ferramenta — pode ser uma falha temporária.\n"
            )
        elif "tool" in err_lower and "não encontrada" in err_lower:
            instrucao_correcao += (
                "ERRO DE FERRAMENTA: você chamou uma ferramenta que não existe. "
                f"As ferramentas disponíveis são: {[t.name for t in tools_list]}. Escolha uma delas.\n"
            )
        else:
            instrucao_correcao += (
                f"ERRO GENÉRICO na ferramenta: {erro[:200]}. "
                "Tente uma abordagem diferente ou use outra ferramenta para obter os dados necessários.\n"
            )

    if not instrucao_correcao:
        instrucao_correcao = (
            "Algumas ferramentas retornaram resultados inesperados. "
            "Revise os parâmetros e tente novamente ou use ferramentas alternativas."
        )

    # Injeta mensagem corretiva como HumanMessage para guiar o próximo ciclo ReAct
    msg_correcao = HumanMessage(
        content=(
            f"[AUTOCORREÇÃO — Ciclo {tentativas + 1}/{MAX_AUTOCORRECOES}]\n"
            f"{instrucao_correcao.strip()}\n\n"
            "Por favor, corrija os parâmetros e continue a investigação usando as ferramentas disponíveis."
        )
    )

    passo = f"AutoCorreção #{tentativas + 1}: {len(erros_encontrados)} erro(s) detectado(s) → instrução corretiva injetada"

    return {
        "messages": [msg_correcao],
        "passos_executados": [passo],
        "tentativas_autocorrecao": tentativas + 1,
    }


# ── Roteamento condicional do Supervisor ────────────────────────────────────
def _route_supervisor(state: AuditoriaGraphState):
    """Se o LLM ainda quer chamar tools, vai para FerraRegras. Senão, vai para Revisao."""
    msgs = state.get("messages", [])
    last = msgs[-1] if msgs else None
    if last and getattr(last, "tool_calls", None):
        return "FerraRegras"
    return "Revisao"


# ── Roteamento pós-FerraRegras: Autocorreção ou continua ReAct ────────────────
def _route_ferramentas(state: AuditoriaGraphState):
    """Após executar as tools:
    - Se alguma retornou erro E ainda há budget de autocorreção → AutoCorrecao
    - Caso contrário → Supervisor (continua o loop ReAct normalmente)
    """
    from langchain_core.messages import ToolMessage
    msgs = state.get("messages", [])
    tentativas = state.get("tentativas_autocorrecao", 0)

    # Verifica se há erros nas ToolMessages da última rodada
    tem_erro = False
    for msg in reversed(msgs):
        if not isinstance(msg, ToolMessage):
            break  # Chegou fora das tool messages — para aqui
        try:
            parsed = json.loads(msg.content)
            if parsed.get("status") == "error":
                tem_erro = True
                break
        except Exception:
            if "error" in msg.content.lower():
                tem_erro = True
                break

    if tem_erro and tentativas < MAX_AUTOCORRECOES:
        return "AutoCorrecao"
    return "Supervisor"


def _route_revisao(state: AuditoriaGraphState):
    """Após HITL: aprovado → Finalização; rejeitado → END."""
    if state.get("aprovado_pelo_usuario", False):
        return "Finalizacao"
    return END


# ── Construção do Grafo ───────────────────────────────────────────────────────
workflow = StateGraph(AuditoriaGraphState)

workflow.add_node("Extrator", extrator_heuristico_node)
workflow.add_node("Supervisor",    supervisor_node)
workflow.add_node("FerraRegras",   ferramentas_node)
workflow.add_node("AutoCorrecao",  autocorrecao_node)   # ← Tarefa 3
workflow.add_node("Revisao",       revisao_node)
workflow.add_node("Finalizacao",   finalizacao_node)

workflow.set_entry_point("Extrator")
workflow.add_edge("Extrator", "Supervisor")

workflow.add_conditional_edges("Supervisor", _route_supervisor, {
    "FerraRegras": "FerraRegras",
    "Revisao":     "Revisao",
})

# Após executar as tools: verifica erros → autocorrect ou ReAct normal
workflow.add_conditional_edges("FerraRegras", _route_ferramentas, {
    "AutoCorrecao": "AutoCorrecao",
    "Supervisor":   "Supervisor",
})

# Autocorreção injeta mensagem e volta para o Supervisor (ReAct continua)
workflow.add_edge("AutoCorrecao", "Supervisor")

workflow.add_conditional_edges("Revisao", _route_revisao, {
    "Finalizacao": "Finalizacao",
    END:           END,
})
workflow.add_edge("Finalizacao", END)

# Compila com checkpointer e pausa HITL antes de Revisao
graph_app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["Supervisor", "Revisao"]
)
