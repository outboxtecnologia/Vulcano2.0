import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("""
    SELECT 
        EXTRACT(YEAR FROM COMPET), 
        EXTRACT(MONTH FROM COMPET), 
        COUNT(*)
    FROM TERCEIROPGTOESOCIAL
    WHERE COMPET >= '2023-01-01'
    GROUP BY 1, 2
    ORDER BY 1, 2
""")
print("\nTERCEIROPGTOESOCIAL (ALL COMPANIES):")
for r in cur.fetchall():
    print(r)
