with open(r'backend/core/agents/auditoria_graph.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Modificar o supervisor para embutir as Heurísticas de Python
old_block = '''def supervisor_node(state: AuditoriaGraphState):
    llm = get_agent_llm().bind_tools(tools_list)
    conta = state.get("conta_alvo", "conta desconhecida")

    # Verifica se já temos um prompt calibrado injetado pelo usuario
    custom_sys_prompt = state.get("prompt_calibracao", "")
    active_system_prompt = custom_sys_prompt if custom_sys_prompt else SYSTEM_PROMPT

    messages = [SystemMessage(content=active_system_prompt + "\\n\\nConta alvo: " + conta)]
    hist = state.get("messages", [])
    
    # Se ainda n houveram ferramentas executadas e chcemos a HITL calibracao
    if not hist and not custom_sys_prompt:
        # Eh o inicio do node, vamos pausar para HitL calibração do prompt.
        # Nós salvamos o default na state e redirecionamos pro HITL
        return {"prompt_calibracao": active_system_prompt, "passos_executados": ["Pausado para Calibração de Prompt Inicial"]}'''

new_block = '''def supervisor_node(state: AuditoriaGraphState):
    llm = get_agent_llm().bind_tools(tools_list)
    conta = state.get("conta_alvo", "conta desconhecida")

    custom_sys_prompt = state.get("prompt_calibracao", "")
    active_system_prompt = custom_sys_prompt if custom_sys_prompt else SYSTEM_PROMPT

    hist = state.get("messages", [])
    
    if not hist and not custom_sys_prompt:
        # Forçar agregação heurística (Dossiê Temporal PY) antes do LLM
        from core.services.combinatorial_analyzer import IFRS15Analyzer
        import json
        
        # Tentar extrair o ID do Empreendimento (Centro de Custo), como Ex: Stuttgart = 35
        # Hack temporário: assumiremos CC 35 por default se o LLM n foi chamado. O ideal é o usá-lo na view.
        # Mas vamos testar o cc_empreendimento = 35 fixo no dossiê de calibração para garantir a amostra do Stuttgart.
        try:
            dossie = IFRS15Analyzer.gerar_dossie_temporal(35, 959, limite_amostra=5)
            str_dossie = "\\n\\n--- DOSSIÊ HEURÍSTICO PYTHON (Amostra 5 unidades - CC: 35) ---\\n" + json.dumps(dossie, ensure_ascii=False, indent=2)
        except Exception as e:
            str_dossie = "\\n\\n(Falhou ao processar dossiê heurístico no supervisor: " + str(e) + ")"

        prompt_com_amostra = active_system_prompt + "\\n\\nConta alvo: " + conta + str_dossie
        
        return {"prompt_calibracao": prompt_com_amostra, "passos_executados": ["Pausado para Calibração do Prompt e Dataset Python"]}

    messages = [SystemMessage(content=active_system_prompt + "\\n\\nConta alvo: " + conta)]
    messages.extend(hist)'''

if "def supervisor_node(state: AuditoriaGraphState):" in text:
    text = text.replace(old_block, new_block)
    with open(r'backend/core/agents/auditoria_graph.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Graph node updated for dossier inline")
else:
    print("Could not find block.")
