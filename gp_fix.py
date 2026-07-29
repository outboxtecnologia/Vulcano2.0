with open(r'backend/core/agents/auditoria_graph.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# We will create a new node called 'extrator_heuristico_node'
new_node_code = '''
def extrator_heuristico_node(state: AuditoriaGraphState):
    """
    Roda apenas uma vez no inicio do Grafo: Extrai os dados do Firebird/SQLite,
    monta a matriz temporal (Dossiê) e formata o prompt de calibração para o HITL.
    """
    conta = state.get("conta_alvo", "")
    active_system_prompt = state.get("prompt_calibracao") or auditoria_system_prompt
    
    if not state.get("dossie_heuristico"):
        try:
            dossie = IFRS15Analyzer.gerar_dossie_temporal(35, 959, limite_amostra=5)
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
    final_prompt = state.get("prompt_calibracao") or auditoria_system_prompt
    
    messages = [SystemMessage(content=final_prompt)]
    historico_msgs = state.get("messages", [])
    # Rehidrata MSGS antigas se precisar (simplificado)
    messages.extend(historico_msgs)
    
    if state.get("sugestao_correcao"):
        messages.append(HumanMessage(content=f"Dica p/ autocorreção: {json.dumps(state['sugestao_correcao'])}"))
        
    print("[Supervisor] Chamando Vertex AI...")
    response = llm.invoke(messages)
    
    return {"messages": [response], "passos_executados": ["Supervisor (LLM) avaliou os dados e tomou decisão."]}
'''

# Substitute the old supervisor_node
text = re.sub(r'def supervisor_node.*?return \{"messages": \[response\], "passos_executados": \["Supervisor \(LLM\) avaliou os dados\."\]\}', new_node_code, text, flags=re.DOTALL)

# Update node mapping
text = text.replace('workflow.add_node("Supervisor",    supervisor_node)', 'workflow.add_node("Extrator", extrator_heuristico_node)\nworkflow.add_node("Supervisor",    supervisor_node)')

# Fix entrypoint
entry_old = 'workflow.set_entry_point("Supervisor")'
entry_new = '''workflow.set_entry_point("Extrator")
workflow.add_edge("Extrator", "Supervisor")'''
text = text.replace(entry_old, entry_new)

# Add "Supervisor" to the interrupts
text = text.replace('interrupt_before=["Revisao"]', 'interrupt_before=["Supervisor", "Revisao"]')

with open(r'backend/core/agents/auditoria_graph.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Splitted Graph successful. Extrator extracted before LLM pause.")
