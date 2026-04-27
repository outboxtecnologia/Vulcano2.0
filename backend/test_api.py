import asyncio
from httpx import AsyncClient

async def test():
    async with AsyncClient() as client:
        r2 = await client.get("http://127.0.0.1:8000/api/questor/contabilizacoes?empresa_id=22&mes=7&ano=2024", timeout=30.0)
        json_resp = r2.json()
        data = json_resp.get("data", [])
        if data:
            print("Empreendimento:", data[0].get("empreendimento"))
            print("Qtd Físicas (Questor):", len(data[0].get("contas_fisicas", [])))
            print("Qtd Legado (Vulcano 1.0):", len(data[0].get("contas_legado", [])))
            print("Qtd Virtuais (IFRS 15):", len(data[0].get("contas_virtuais", [])))
        else:
            print("Returned array 'data' is EMPTY!")

if __name__ == "__main__":
    asyncio.run(test())
