"""
Simula EXATAMENTE o pipeline api_contabilizacoes para o Stuttgart
e verifica se a conta 5639 aparece em contas_virtuais com o saldo correto.
"""
import sys, os
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("backend/core/services"))

from dotenv import load_dotenv
load_dotenv("backend/.env", override=True)

# Importa o pipeline
from core.services.graph_logic_builder import AccountingGraphPipeline

print("Chamando AccountingGraphPipeline.api_contabilizacoes...")
print("emp=335 (Stuttgart), 2025-03, empresa=959")
print("=" * 65)

try:
    resultado = AccountingGraphPipeline.api_contabilizacoes(
        ano=2025, mes=3, empresa_id=959, empreendimento_id="335"
    )
    resultado_raw = resultado if isinstance(resultado, list) else [resultado]
    print(f"\nTipo resultado: {type(resultado)}")
    print(f"Len: {len(resultado_raw)}")
    if resultado_raw:
        first = resultado_raw[0]
        print(f"Tipo do primeiro item: {type(first)}")
        if isinstance(first, dict):
            print(f"Chaves: {list(first.keys())}")
        elif isinstance(first, str):
            # pode ser lista de nomes
            print(f"Primeiro item é string: {first[:100]}")
            # talvez o resultado seja um dict com 'empreendimentos'
            print(f"Resultado raw: {str(resultado)[:500]}")

        if not isinstance(emp_r, dict):
            print(f"  Tipo inesperado: {type(emp_r)} — {str(emp_r)[:200]}")
            continue
        print(f"\n  [{emp_r.get('empreendimento_id','?')}] {emp_r.get('empreendimento_nome','?')}")
        virtuais = emp_r.get("contas_virtuais", [])
        fisicas  = emp_r.get("contas_fisicas", [])
        print(f"  contas_virtuais: {len(virtuais)} | contas_fisicas: {len(fisicas)}")

        conta_5639_v = next((c for c in virtuais if c.get("conta") == 5639), None)
        conta_5639_f = next((c for c in fisicas  if c.get("conta") == 5639), None)

        if conta_5639_v:
            print(f"\n  [VIRTUAL 5639] saldo_anterior={conta_5639_v['saldo_anterior']:,.2f} "
                  f"mov_deb={conta_5639_v['movimento_debito']:,.2f} "
                  f"saldo_final={conta_5639_v['saldo_final']:,.2f}")
        else:
            print(f"\n  [VIRTUAL 5639] NAO ENCONTRADA")

        if conta_5639_f:
            print(f"  [FISICA  5639] saldo_anterior={conta_5639_f['saldo_anterior']:,.2f} "
                  f"mov_deb={conta_5639_f['movimento_debito']:,.2f} "
                  f"saldo_final={conta_5639_f['saldo_final']:,.2f} "
                  f"({len(conta_5639_f.get('detalhes',[]))} lançamentos)")
        else:
            print(f"  [FISICA  5639] NAO ENCONTRADA")

except Exception as e:
    import traceback
    print(f"ERRO: {e}")
    traceback.print_exc()
