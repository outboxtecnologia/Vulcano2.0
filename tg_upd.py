with open(r'backend/core/agents/auditoria_graph.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '''return {"prompt_calibracao": prompt_com_amostra, "passos_executados": ["Pausado para Calibração do Prompt e Dataset Python"]}''',
    '''return {"prompt_calibracao": prompt_com_amostra, "passos_executados": ["Pausado para Calibração.\\n\\n  Python coletou com sucesso o Fluxo e Custo de 5 Unidades da matriz (Verifique o arquivo na caixa verde no rogapé!)"]}'''
)

with open(r'backend/core/agents/auditoria_graph.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated steps")
