import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("""
    SELECT COUNT(*) FROM TERCEIROPGTOSERVICO S
    LEFT JOIN TERCEIROPGTO T ON S.CODIGOEMPRESA = T.CODIGOEMPRESA 
        AND S.CODIGOTERC = T.CODIGOTERC 
        AND S.COMPET = T.COMPET 
        AND S.SEQ = T.SEQ
    WHERE T.CODIGOEMPRESA IS NULL
""")
print("Orphan S rows:", cur.fetchone())
