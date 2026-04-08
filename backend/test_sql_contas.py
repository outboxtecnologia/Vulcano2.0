import sys
sys.path.append('backend')
from main import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()

try:
    cur.execute("""
        SELECT FIRST 1 
            CONTACLI, CONTAADICLI, CONTAREC, CONTADESPESA, CONTACAIXA, 
            CONTAVARIACAO, CONTAESTAND, CONTAESTCON, CONTACUSTO, 
            CONTADEVOLUCAO, CONTALUCROACUM, CONTA_ESTORNO_DEVOLUCAO 
        FROM EMPREENDIMENTO
    """)
    rows = cur.fetchall()
    print("Columns exist and data fetched ok!")
    print(rows)
except Exception as e:
    import traceback
    traceback.print_exc()
