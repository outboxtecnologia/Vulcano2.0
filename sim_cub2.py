import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import main
conn = main.get_conn('vulcano')
cur = conn.cursor()
cur.execute("SELECT ID_INDICE_REAJUSTE, EXTRACT(YEAR FROM MES), COUNT(*) FROM INDICE_REAJUSTE_TABELA GROUP BY 1, 2 ORDER BY 1, 2")
rows = cur.fetchall()
print("Indices Available:")
for r in rows:
    print(f"ID {r[0]} | Year: {r[1]} | Count: {r[2]}")
conn.close()
