import sys
sys.path.append('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend')
from main import get_conn
conn = get_conn('vulcano')
cur = conn.cursor()
try:
    cur.execute("""
        SELECT 
            EXTRACT(YEAR FROM V.DTOPER) as ANO,
            EXTRACT(MONTH FROM V.DTOPER) as MES,
            COUNT(VU.ID) as QTD_VENDIDA
        FROM VENDAUNIDADE VU 
        JOIN VENDA V ON V.ID = VU.IDVENDA 
        JOIN UNIDADE U ON U.ID = VU.IDUNIDADE 
        JOIN BLOCO B ON B.ID = U.IDBLOCO 
        WHERE B.IDEMPREENDIMENTO = ? AND COALESCE(V.DISTRATO, 'N') NOT IN ('T', 'S', '1')
        GROUP BY 1, 2
        ORDER BY 1 ASC, 2 ASC
    """, (153,))
    print(cur.fetchall())
except Exception as e:
    print('Error:', str(e))
