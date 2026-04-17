import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import asyncio
from main import app, api_agentes_iniciar, AuditResumeReq

async def run_api():
    req = AuditResumeReq(conta_alvo="Conta 5639")
    resp = await api_agentes_iniciar(req)
    print("API Response Keys:", resp.keys())
    print("State Keys:", resp.get("state", {}).keys())

asyncio.run(run_api())
