import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn
from core.services.combinatorial_analyzer import IFRS15Analyzer

conn_v, conn_q = get_conn(), get_conn("questor")
cur_v, cur_q = conn_v.cursor(), conn_q.cursor()

dossie = IFRS15Analyzer.gerar_dossie_temporal(
    cur_v=cur_v,
    cur_q=cur_q,
    cc_empreendimento=35,
    empresa_id=959,
    nome_emp="STUTTGART",
    conta_estoque="5639",
    # Just mock something to skip error if missing arguments
    tabela_cc=35
)

# Find APTO 201
apto201 = next((u for u in dossie['unidades'] if '201' in u['unidade']), None)
if apto201:
    print("APTO 201 GRID TEMPORAL:")
    for g in apto201['grid_temporal']:
        if g.get('credito_questor'):
            print(f"{g['ano']}-{g['mes']}: {g['credito_questor']}")
else:
    print("Apto 201 missing!")
