import asyncio
from httpx import AsyncClient

async def test():
    async with AsyncClient() as client:
        r = await client.get("http://127.0.0.1:8000/openapi.json", timeout=10.0)
        schema = r.json()
        paths = schema.get("paths", {})
        for p, methods in paths.items():
            if "agentes" in p:
                print(p, list(methods.keys()))

if __name__ == "__main__":
    asyncio.run(test())
