import sys, os
sys.path.insert(0, os.path.abspath('backend'))
import asyncio
from core.services.graph_logic_builder import AccountingGraphPipeline

async def run():
    try:
        res = AccountingGraphPipeline.api_contabilizacoes(2025, 3, 959, None)
        print("Keys returned:", res.keys())
        loc = [x for x in res['data'] if 'GLOBAL_LOC' in str(x.get('empreendimento_id', ''))]
        if not loc:
            print("GLOBAL_LOC not found!")
            return
        loc_data = loc[0]
        virtuais = loc_data.get('contas_virtuais', [])
        print(f"Total contas em Locações: {len(virtuais)}")
        for c in virtuais:
            print(f"ID={c['conta']} D={c.get('movimento_debito',0):.2f} C={c.get('movimento_credito',0):.2f} Ant={c.get('saldo_anterior',0):.2f}")
    except Exception as e:
        import traceback
        traceback.print_exc()

run()
