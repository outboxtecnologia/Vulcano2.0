import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import main
from core.services.graph_logic_builder import AccountingGraphPipeline

import asyncio
res = asyncio.run(AccountingGraphPipeline.api_contabilizacoes(2024, 12, 959, '35'))
print(len(res))
