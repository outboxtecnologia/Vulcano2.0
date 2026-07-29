import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn
from core.services.combinatorial_analyzer import IFRS15Analyzer

try:
    conn_v, conn_q = get_conn(), get_conn("questor")
    cur_v, cur_q = conn_v.cursor(), conn_q.cursor()

    dossie = IFRS15Analyzer.gerar_dossie_temporal(
        cc_empreendimento=35,
        empresa_id=959,
        conta_alvo="5639",
    )
    print("KEYS:", dossie.keys())
    if "amostra_unidades" in dossie:
        print("TEM AMOSTRA!")
    else:
        print("FALHOU!", dossie)
except Exception as e:
    import traceback
    traceback.print_exc()
