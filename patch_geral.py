import os
with open('backend/core/services/graph_logic_builder.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '"cc": empreendimento_id or "GERAL"',
    '"cc": empreendimento_id or 0'
)

with open('backend/core/services/graph_logic_builder.py', 'w', encoding='utf-8') as f:
    f.write(code)
