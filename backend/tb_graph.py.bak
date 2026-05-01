import json
import sys

with open(r'core/agents/auditoria_graph.py', 'r', encoding='utf-8') as f:
    text = f.read()

# updating imports
if "calcular_custo_realizado_poc_metragem" not in text:
    old_import = "analisar_estoque_lctoger,\n    agrupar_creditos_por_apto,"
    new_import = "analisar_estoque_lctoger,\n    agrupar_creditos_por_apto,\n    calcular_custo_realizado_poc_metragem,"
    text = text.replace(old_import, new_import)

# updating tools_list
if "calcular_custo_realizado_poc_metragem" in text and "calcular_custo_realizado_poc_metragem," not in text.split("tools_list = [")[1]:
    old_tool_list = "analisar_estoque_lctoger,\n    agrupar_creditos_por_apto,"
    new_tool_list = "analisar_estoque_lctoger,\n    agrupar_creditos_por_apto,\n    calcular_custo_realizado_poc_metragem,"
    text = text.replace(old_tool_list, new_tool_list)

# Updating prompt Rule 9
if "calcular_custo_realizado_poc_metragem(cc_empreendimento)" not in text:
    old_prompt_str = "financeiro mas estimativa de custo incorrido."
    new_prompt_str = "financeiro mas estimativa de custo incorrido.\n9. OBRIGATÓRIO: Para testar a exatidão fracionária do Estoque, chame calcular_custo_realizado_poc_metragem(cc_empreendimento). Se a unidade bater perfeitamente com a rubrica 	este_distorcao_com_poc em vez de custo_correto_ifrs15, AONDE HOUVER erro, a recomendação (acao) é refazer o custeio: a empresa aplicou o % de POC sobre a mensuração do custo inadvertidamente."
    text = text.replace(old_prompt_str, new_prompt_str)

with open(r'core/agents/auditoria_graph.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Graph atualizado.")
