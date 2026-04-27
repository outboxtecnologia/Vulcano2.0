import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import main
conn = main.get_conn('vulcano')
cur = conn.cursor()
cur.execute("SELECT EXTRACT(YEAR FROM MES), EXTRACT(MONTH FROM MES), PERCENTUAL_VARIACAO FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1")
rows = cur.fetchall()
print("CUB rows:", len(rows))
if rows:
    print("Sample:", rows[:5])
conn.close()
