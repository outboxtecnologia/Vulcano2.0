import sys, fdb
try:
    conn = fdb.connect(dsn='127.0.0.1:C:/Vulcano/Database/VULCANO.FDB', user='SYSDBA', password='masterkey', charset='UTF8')
    cur = conn.cursor()
    cur.execute('''SELECT 
            (SELECT SUM(U.METRAGEM) FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = 5) as TOTAL_AREA,
            (SELECT SUM(U.METRAGEM) FROM VENDAUNIDADE VU JOIN VENDA V ON V.ID = VU.IDVENDA JOIN UNIDADE U ON U.ID = VU.IDUNIDADE JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = 5 AND COALESCE(V.DISTRATO, 'N') NOT IN ('T', 'S', '1')) as SOLD_AREA
        FROM RDB$DATABASE''')
    res = cur.fetchone()
    print('RESULT:')
    print(res)
except Exception as e:
    print('ERROR:')
    print(e)
