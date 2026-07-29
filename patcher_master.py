import os
import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# ----------------- PHASE 1: RevenueTimePipeline -----------------
start1 = text.find('def get_receitas_caixa(')
# Find end of get_receitas_caixa
# it ends at the next root-level def (like def foo) or @app.
match1 = re.search(r'\n(?:@app|def )', text[start1+1:])
end1 = start1 + 1 + match1.start()
func1 = text[start1:end1]

with open('backend/core/services/revenue_time_pipeline.py', 'w', encoding='utf-8') as f:
    f.write('''import pandas as pd\nimport numpy as np\nimport collections\nimport datetime\nfrom fastapi import HTTPException\n\nclass RevenueTimePipeline:\n    @staticmethod\n''')
    inject_imports = '        from backend.main import get_conn, safe_decode, get_poc_strictly_before, get_poc_at_or_before, fmt_cta\n        import traceback'
    func1 = func1.replace('import collections\n        import datetime', 'import collections\n        import datetime\n' + inject_imports)
    f.write('    ' + func1.replace('\n', '\n    ').replace('    def get_receitas_caixa', 'def get_receitas_caixa'))

mock1 = '''from core.services.revenue_time_pipeline import RevenueTimePipeline\n\n@app.get("/api/receitas-caixa")\ndef get_receitas_caixa_api(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, empreendimentos_ids: str | None = None):\n    return RevenueTimePipeline.get_receitas_caixa(empresa_id, data_ini, data_fim, empreendimentos_ids)'''

# Replace @app.get("/api/receitas-caixa")\ndef get_receitas_caixa( to end
text = re.sub(r'@app\.get\("/api/receitas-caixa"\)\ndef get_receitas_caixa\(.*?(?=\n(?:@app|def ))', mock1, text, flags=re.DOTALL)

# ----------------- PHASE 1: AccountingGraphPipeline -----------------
start2 = text.find('def api_contabilizacoes(')
match2 = re.search(r'\n(?:@app|def )', text[start2+1:])
end2 = start2 + 1 + match2.start()
func2 = text[start2:end2]

with open('backend/core/services/graph_logic_builder.py', 'w', encoding='utf-8') as f:
    f.write('''import traceback\nfrom datetime import datetime\nfrom collections import defaultdict\nfrom fastapi import HTTPException\n\nclass AccountingGraphPipeline:\n    @staticmethod\n''')
    inject2 = '\n        from backend.main import get_conn, safe_decode, fmt_cta, get_poc_strictly_before, get_poc_at_or_before, get_receitas_caixa_api\n'
    func2 = func2.replace('def api_contabilizacoes(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, min_divergencia: float = 0.0, limit: int = 100):', 'def api_contabilizacoes(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, min_divergencia: float = 0.0, limit: int = 100):' + inject2)
    f.write('    ' + func2.replace('\n', '\n    ').replace('    def api_contabilizacoes', 'def api_contabilizacoes'))

mock2 = '''from core.services.graph_logic_builder import AccountingGraphPipeline\n\n@app.get("/api/questor/contabilizacoes")\ndef api_contabilizacoes(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, min_divergencia: float = 0.0, limit: int = 100):\n    return AccountingGraphPipeline.api_contabilizacoes(empresa_id, data_ini, data_fim, min_divergencia, limit)'''

text = re.sub(r'@app\.get\("/api/questor/contabilizacoes"\)\ndef api_contabilizacoes\(.*?(?=\n(?:@app|def ))', mock2, text, flags=re.DOTALL)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
