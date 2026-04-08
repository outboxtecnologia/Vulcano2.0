import sys, traceback
try:
    import fdb
    conn = fdb.connect(dsn='127.0.0.1:C:/Vulcano/Database/VULCANO.FDB', user='SYSDBA', password='masterkey', charset='UTF8')
    cur = conn.cursor()
    
    cur.execute('SELECT SUM(U.METRAGEM) FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = 5')
    r1 = cur.fetchone()
    
    cur.execute("SELECT SUM(U.METRAGEM) FROM VENDAUNIDADE VU JOIN VENDA V ON V.ID = VU.IDVENDA JOIN UNIDADE U ON U.ID = VU.IDUNIDADE JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = 5 AND COALESCE(V.DISTRATO, 'N') NOT IN ('T', 'S', '1')")
    r2 = cur.fetchone()
    
    with open('output_area.txt', 'w', encoding='utf-8') as f:
        f.write(f"R1: {r1}\n")
        f.write(f"R2: {r2}\n")

except Exception as e:
    with open('output_area.txt', 'w', encoding='utf-8') as f:
        f.write("ERR: " + str(e) + "\n" + traceback.format_exc())
