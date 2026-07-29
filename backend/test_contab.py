import sys
sys.path.append(r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend')
import asyncio
from core.services.graph_logic_builder import AccountingGraphPipeline

async def run_test():
    res = AccountingGraphPipeline.api_contabilizacoes(ano=2025, mes=3, empresa_id=959)
    if 'data' not in res or not res['data']:
        print('Nenhum dado retornado.')
        return
        
    fisicas = res['data'][0].get('contas_fisicas', [])
    print(f'Total contas fisicas: {len(fisicas)}')
    
    # Procura a conta 5639 (Stuttgart)
    c_5639 = next((c for c in fisicas if c['conta'] == 5639), None)
    if c_5639:
        print('CONTA 5639 ENCONTRADA!')
        print(f'  Saldo Anterior: {c_5639["saldo_anterior"]}')
        print(f'  Mov Liquido: {c_5639["movimento_liquido"]}')
        print(f'  Saldo Final: {c_5639["saldo_final"]}')
        if c_5639.get('detalhes'):
            print(f'  Total Lançamentos: {len(c_5639["detalhes"])}')
            for d in c_5639['detalhes'][:3]:
                print(f'    > {d["data"]} | {d["natureza"]} | {d["valor"]} | {d["historico"]}')
    else:
        print('Conta 5639 NAO encontrada nas contas_fisicas.')

asyncio.run(run_test())
