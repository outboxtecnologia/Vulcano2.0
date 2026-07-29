import os

with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = 977
end_idx = 1894

func_code = ''.join(lines[start_idx:end_idx])

new_main = lines[:start_idx] + [
    '\n# DECOUPLED: AccountingGraphPipeline -> graph_logic_builder\n',
    'from core.services.graph_logic_builder import AccountingGraphPipeline\n',
    'api_contabilizacoes_impl = AccountingGraphPipeline.api_contabilizacoes\n\n',
    '@app.get("/api/questor/contabilizacoes")\n',
    'def api_contabilizacoes(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, min_divergencia: float = 0.0, limit: int = 100):\n',
    '    return api_contabilizacoes_impl(empresa_id, data_ini, data_fim, min_divergencia, limit)\n\n'
] + lines[end_idx:]

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_main)

header = '''import traceback
from datetime import datetime
from collections import defaultdict
from fastapi import HTTPException

class AccountingGraphPipeline:
'''

func_code = func_code.replace('@app.get("/api/questor/contabilizacoes")\n', '')

# add dependency injection inside the function to avoid circular logic
inject = '''
        from backend.main import (
            get_conn, safe_decode, fmt_cta, get_poc_strictly_before, get_poc_at_or_before,
            get_receitas_caixa_api
        )
'''
func_code = func_code.replace('def api_contabilizacoes(', 'def api_contabilizacoes(')

final_code = header + '    @staticmethod\n' + '    ' + func_code.replace('\n', '\n    ').replace('    def api_contabilizacoes', 'def api_contabilizacoes')
# inject the imports immediately after def
final_code = final_code.replace('    def api_contabilizacoes(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, min_divergencia: float = 0.0, limit: int = 100):', '    def api_contabilizacoes(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, min_divergencia: float = 0.0, limit: int = 100):' + inject)

with open('backend/core/services/graph_logic_builder.py', 'w', encoding='utf-8') as f:
    f.write(final_code)
