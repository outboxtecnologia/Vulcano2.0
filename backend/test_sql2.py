import sys
sys.path.append('backend')
from main import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()

query = """
    SELECT 
        v.CODIGOEMPRESA,
        v.CODIGOESTAB,
        e.NOME AS EMPREENDIMENTO,
        v.UNIDIMOB AS UNIDADE,
        c.NOME AS COMPRADOR,
        r.DATA AS DATA_RECEBIMENTO,
        r.TOTALPAGO AS RECEITA_CAIXA,
        v.TOTALVENDA AS VGV_BASE,
        e.RET,
        v.DISTRATO,
        v.DATADISTRATO
    FROM VENDA v
    JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
    LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
    LEFT JOIN RECEBER r ON r.IDVENDA = v.ID AND r.TOTALPAGO > 0
    WHERE v.CODIGOEMPRESA = 1
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
