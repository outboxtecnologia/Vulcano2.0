import asyncio
import sys, os
sys.path.insert(0, os.path.abspath('backend'))
from core.database.connection import get_conn
from core.services.graph_logic_builder import AccountingGraphPipeline

async def run():
    pipe = AccountingGraphPipeline()
    res = await pipe.api_contabilizacoes('959', '3', '2025', 'todas')
    
    # Let's inspect the injected Virtual accounts data
    virtuais = res['data'][0]['contas_virtuais']
    for v in virtuais:
        print(f"Conta: {v['conta']} - Deb: {v['movimento_debito']} - Cred: {v['movimento_credito']}")

asyncio.run(run())
