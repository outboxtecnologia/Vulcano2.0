import asyncio
from httpx import AsyncClient

async def test():
    async with AsyncClient() as client:
        print("Testing Without Trailing Slash...")
        r1 = await client.post("http://127.0.0.1:8000/api/agentes/iniciar_auditoria", json={"conta_alvo": "Conta 5639 - IMÓVEIS A CONCLUIR"}, timeout=10.0)
        print("Status", r1.status_code)
        
        print("Testing With Trailing Slash...")
        r2 = await client.post("http://127.0.0.1:8000/api/agentes/iniciar_auditoria/", json={"conta_alvo": "Conta 5639 - IMÓVEIS A CONCLUIR"}, timeout=10.0)
        print("Status", r2.status_code)

if __name__ == "__main__":
    asyncio.run(test())
