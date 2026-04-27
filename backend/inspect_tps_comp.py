import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("""
    SELECT 
        CODIGOEMPRESA,
        EXTRACT(YEAR FROM COMPET), 
        EXTRACT(MONTH FROM COMPET), 
        COUNT(*)
    FROM TERCEIROPGTOSERVICO
    WHERE COMPET >= '2023-01-01'
    GROUP BY 1, 2, 3
    ORDER BY 1, 2, 3
""")
print("\nTERCEIROPGTOSERVICO BY COMPANY:")
for r in cur.fetchall():
    print(r)
