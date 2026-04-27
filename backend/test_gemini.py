import asyncio
import sys
sys.path.append(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import _gemini_generate_json_async, _require_gemini_key
import os

async def test():
    try:
        from dotenv import load_dotenv
        load_dotenv(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\.env")
        _require_gemini_key()
        res = await _gemini_generate_json_async('{"causa_raiz": "Teste"}', mime_type="application/json")
        print("SUCCESS:", res)
    except Exception as e:
        print("ERROR:", e)

asyncio.run(test())
