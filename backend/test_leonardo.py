import sys
sys.path.append('backend')
from main import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()

query = """
    SELECT 
        v.CODIGOEMPRESA,
        e.NOME AS EMPREENDIMENTO,
        v.UNIDIMOB AS UNIDADE,
        c.NOME AS COMPRADOR,
        v.TOTALVENDA AS VGV_BASE,
        v.ID AS IDVENDA,
        SUM(r.TOTALPAGO) as PAGO
    FROM VENDA v
    JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
    LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
    LEFT JOIN RECEBER r ON r.IDVENDA = v.ID AND r.TOTALPAGO > 0
    WHERE c.NOME LIKE '%LEONARDO NIENKOTTER%' AND v.CODIGOEMPRESA = 959
    GROUP BY 1,2,3,4,5,6
"""

try:
    cur.execute(query)
    rows = cur.fetchall()
    print(f"Found {len(rows)} contracts for Leonardo Nienkotter:")
    for r in rows:
        print(r)
except Exception as e:
    import traceback
    traceback.print_exc()
