import sys
sys.path.insert(0, r"backend")
from core.database.connection import get_conn
import asyncio
from core.services.graph_logic_builder import AccountingGraphPipeline

async def run():
    pipe = AccountingGraphPipeline()
    res = await pipe.api_contabilizacoes('959', '3', '2025', 'todas', None)
    print(res)

asyncio.run(run())
