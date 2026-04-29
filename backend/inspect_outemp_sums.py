import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("""
    SELECT FIRST 10 
        COMPET, 
        CODIGOOUTEMP,
        SUM(BASEGPS), 
        SUM(VALORBRUTO)
    FROM OUTRAEMPPGTOSERVICO
    WHERE CODIGOEMPRESA = 959 AND COMPET >= '2023-01-01'
    GROUP BY COMPET, CODIGOOUTEMP
    ORDER BY COMPET
""")
print("\nOUTRAEMPPGTOSERVICO OUTEMP SUMS:")
for r in cur.fetchall():
    print(r)
