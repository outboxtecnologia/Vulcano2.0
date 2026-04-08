import sys
sys.path.append('.')
from main import get_conn

try:
    conn = get_conn('vulcano')
    cur = conn.cursor()
    cur.execute("SELECT FIRST 10 MES, PERCENTUAL_VARIACAO, VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND VALOR IS NOT NULL ORDER BY MES DESC")
    with open('cub_not_null.txt', 'w') as f:
        for r in cur.fetchall():
            f.write(str(r) + '\n')
except Exception as e:
    with open('cub_err.txt', 'w') as f: f.write(str(e))
finally:
    if 'conn' in locals() and conn: conn.close()
