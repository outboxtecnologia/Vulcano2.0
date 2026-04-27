import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM OUTRAEMPPGTOSERVICO WHERE CODIGOEMPRESA = 959 AND CODIGOOUTEMP = 35")
print('OUTEMP 35 rows:', cur.fetchone())
cur.execute("SELECT COUNT(*) FROM TERCEIROPGTOSERVICO T JOIN TERCEIROPGTO P ON T.CODIGOEMPRESA = P.CODIGOEMPRESA AND T.CODIGOTERC = P.CODIGOTERC AND T.COMPET = P.COMPET AND T.SEQ = P.SEQ WHERE P.CODIGOOUTEMP = 35")
print('OUTEMP 35 rows in TERCEIROPGTOSERVICO:', cur.fetchone())
