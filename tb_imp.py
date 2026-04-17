with open(r'backend/core/agents/auditoria_graph.py', 'r', encoding='utf-8') as f:
    text = f.read()

if "dossie_amostral_unidades_vulcano" not in text:
    old_imp = "calcular_custo_realizado_poc_metragem,"
    new_imp = "calcular_custo_realizado_poc_metragem,\n    dossie_amostral_unidades_vulcano,"
    text = text.replace(old_imp, new_imp)

with open(r'backend/core/agents/auditoria_graph.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Graph imports updated")
