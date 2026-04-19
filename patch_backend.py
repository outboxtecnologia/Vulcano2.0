import os

with open('backend/core/services/graph_logic_builder.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace variables block to initialize them securely
old_block = """                custo_gasto_anterior = 0.0
                custo_gasto_vigente  = 0.0"""

new_block = """                custo_gasto_anterior = 0.0
                custo_gasto_vigente  = 0.0
                mov_debito_mes       = 0.0
                mov_credito_mes      = 0.0"""

code = code.replace(old_block, new_block)

with open('backend/core/services/graph_logic_builder.py', 'w', encoding='utf-8') as f:
    f.write(code)
