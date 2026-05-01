import httpx
import asyncio
import json

async def run():
    async with httpx.AsyncClient() as client:
        resp = await client.get('http://127.0.0.1:8000/api/questor/contabilizacoes?empresa_id=959&mes=3&ano=2025&contas=1939&unidade=todas')
        if resp.status_code == 200:
            data = resp.json()
            stutt = [e for e in data['data'] if 'stuttgart' in str(e['empreendimento_nome']).lower()]
            if stutt:
                for cv in stutt[0]['contas_virtuais']:
                    if cv['conta'] == 1939:
                        print("CONTA 1939 VIRTUAL:", cv['movimento_debito'], cv['movimento_credito'], cv['saldo_anterior'])
                        for det in cv['detalhes']:
                            print("  ", det['data'], det['historico'], det['natureza'], det['valor'])
        else:
            print("HTTP ERRO:", resp.status_code, resp.text)
asyncio.run(run())
