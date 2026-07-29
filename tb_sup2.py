with open(r'backend/core/agents/auditoria_graph.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# We need to replace supervisor_node. Find its block.
match = re.search(r'def supervisor_node\(state: AuditoriaGraphState\):.*?(?=\ndef |#)', text, re.DOTALL)
if match:
    old_method = match.group(0)
    new_method = '''def supervisor_node(state: AuditoriaGraphState):
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
        return {"prompt_calibracao": active_system_prompt, "passos_executados": ["Pausado para Calibração de Prompt Inicial"]}

    messages.extend(hist)

    if state.get("sugestao_correcao"):
        messages.append(HumanMessage(content=f"Dica p/ autocorreção: {json.dumps(state['sugestao_correcao'])}"))

    response = llm.invoke(messages)
    return {"messages": [response], "passos_executados": ["Supervisor (LLM) avaliou os dados."]}
'''
    text = text.replace(old_method, new_method)
    with open(r'backend/core/agents/auditoria_graph.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("supervisor_node modified.")
else:
    print("Match failed.")
