"""
Testa as contabilizações de 04/2025 para verificar o print de estorno do distrato
"""
import sys
sys.path.insert(0, 'backend')
import asyncio
from main import api_contabilizacoes

async def main():
    print("Executando api_contabilizacoes(mes=4, ano=2025, empresa_id=959)...")
    res = await api_contabilizacoes(mes=4, ano=2025, empresa_id=959)
    print("Contabilizações geradas com sucesso!")
    
    # Procura a conta 4995 no Stuttgart (id=335)
    for emp in res.get('data', []):
        if emp.get('empreendimento_id') == 335:
            print(f"Empreendimento: {emp.get('empreendimento_nome')}")
            for c in emp.get('contas_virtuais', []):
                if c.get('conta') == 4995:
                    print(f"  Conta 4995 -> Mov Liquido: R${c.get('movimento_liquido',0):.2f} | Saldo: R${c.get('saldo_final',0):.2f}")
                    for d in c.get('detalhes', []):
                        if 'DISTRATO' in str(d.get('historico','')).upper():
                            print(f"    *** {d.get('natureza')} R${d.get('valor',0):.2f} | {d.get('historico')}")

try:
    asyncio.run(main())
except Exception as e:
    import traceback
    traceback.print_exc()

