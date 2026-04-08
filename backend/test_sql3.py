import sys
sys.path.append('backend')
from main import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()

query = """
    SELECT FIRST 10
        v.CODIGOEMPRESA,
        r.VALORPARCELA,
        r.VALORVARIACAO
    FROM VENDA v
    LEFT JOIN RECEBER r ON r.IDVENDA = v.ID AND r.TOTALPAGO > 0
    WHERE r.TOTALPAGO > 0
"""

try:
    cur.execute(query)
    rows = cur.fetchall()
    print("Found rows:", len(rows))
    if len(rows) > 0:
        print("First row:", rows[0])
except Exception as e:
    import traceback
    traceback.print_exc()
