import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from core.agents.tools import analisar_estoque_lctoger

try:
    print(analisar_estoque_lctoger.invoke({"conta_alvo": "5639", "empresa_id": 959, "cc_empreendimento": 35}))
except Exception as e:
    import traceback
    traceback.print_exc()
