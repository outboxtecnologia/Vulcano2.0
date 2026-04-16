import sys, os
sys.path.insert(0, os.path.abspath('.'))
import asyncio
from core.services.graph_logic_builder import AccountingGraphPipeline

async def run():
    try:
        pipe = AccountingGraphPipeline()
        res = await pipe.api_contabilizacoes('959', '3', '2025', '35')
        stutt = res['data'][0]
        v_caixa = [c for c in stutt.get('contas_virtuais', []) if c.get('is_caixa') or c.get('conta') == 99999]
        for c in v_caixa:
            print(f"ID={c['conta']} D={c.get('movimento_debito', 0):.2f} C={c.get('movimento_credito', 0):.2f} Ant={c.get('saldo_anterior', 0):.2f}")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(run())
