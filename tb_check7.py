import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn
conn_v = get_conn()
cur = conn_v.cursor()
cur.execute('''
    SELECT FIRST 5 U.ID, U.DESCRICAO, U.METRAGEM, V.DTOPER, V.TOTALVENDA
    FROM UNIDADE U
    JOIN BLOCO B ON B.ID = U.IDBLOCO
    JOIN VENDAUNIDADE VU ON VU.IDUNIDADE = U.ID
    JOIN VENDA V ON V.ID = VU.IDVENDA
    WHERE B.IDEMPREENDIMENTO = 335 AND COALESCE(V.DISTRATO, 'N') <> 'S'
    ORDER BY U.ID
''')
print("UNIDADES:", cur.fetchall())
