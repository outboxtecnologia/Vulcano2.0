import sys
sys.path.insert(0, '.')
from main import api_saldo_contas

# Testa contas de resultado (Receita de Venda) para jan 2025
r = api_saldo_contas(empresa_id=959, mes=1, ano=2025, contas='5665,5653,5666,5667,5669')
for item in r['data']:
    nome = item['nome']
    sa   = item['saldo_anterior']
    md   = item['movimento_debito']
    mc   = item['movimento_credito']
    sf   = item['saldo_final']
    nd   = len(item['detalhes'])
    print(f"Conta {item['conta']} [{nome}]")
    print(f"  saldo_anterior : {sa:,.2f}")
    print(f"  mov_debito     : {md:,.2f}")
    print(f"  mov_credito    : {mc:,.2f}")
    print(f"  saldo_final    : {sf:,.2f}")
    print(f"  num_detalhes   : {nd}")
    print()
