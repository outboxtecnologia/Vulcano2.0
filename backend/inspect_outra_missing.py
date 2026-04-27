import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("""
    SELECT COUNT(*) FROM OUTRAEMPPGTO O 
    LEFT JOIN OUTRAEMPPGTOSERVICO S ON O.CODIGOEMPRESA = S.CODIGOEMPRESA 
        AND O.CODIGOOUTEMP = S.CODIGOOUTEMP 
        AND O.COMPET = S.COMPET AND O.SEQ = S.SEQ
    WHERE O.COMPET >= '2023-01-01' AND S.CODIGOEMPRESA IS NULL
""")
print("OUTRAEMPPGTO sem SERVICO:", cur.fetchone())
