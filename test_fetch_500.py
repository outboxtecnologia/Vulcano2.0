import httpx
import asyncio
async def fetch():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get('http://127.0.0.1:8000/api/questor/contabilizacoes?empresa_id=959&mes=3&ano=2025&contas=1939&unidade=todas', timeout=60)
            print(resp.status_code)
            print(resp.text[:500])
    except Exception as e:
        print("Erro de conexao:", e)
asyncio.run(fetch())
