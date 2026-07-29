import sys, os
sys.path.insert(0, os.path.abspath('.'))
import asyncio
from core.database.connection import get_conn
from core.services.graph_logic_builder import AccountingGraphPipeline

async def run():
    try:
        pipe = AccountingGraphPipeline()
        conn = get_conn('questor')
        res = await pipe.api_contabilizacoes('959', '3', '2025', 'todas', None)
        print("OK - length:", len(res['data']))
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(run())
