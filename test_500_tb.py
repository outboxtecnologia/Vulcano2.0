import sys
sys.path.insert(0, r"backend")
from core.database.connection import get_conn
from core.services.graph_logic_builder import AccountingGraphPipeline
import asyncio

async def run():
    try:
        pipe = AccountingGraphPipeline()
        res = await pipe.api_contabilizacoes('959', '3', '2025', 'todas', None)
        print("OK")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(run())
