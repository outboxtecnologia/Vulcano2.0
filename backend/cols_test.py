import firebirdsql
DB_Q = r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB'
con = firebirdsql.connect(host='localhost', port=3050, database=DB_Q, user='SYSDBA', password='masterkey', charset='WIN1252')
cur = con.cursor()
cur.execute('SELECT FIRST 1 * FROM LCTOGER')
print('Colunas LCTOGER:', [d[0] for d in cur.description])
cur.execute('SELECT FIRST 1 * FROM LCTOCTB')
print('Colunas LCTOCTB:', [d[0] for d in cur.description])
con.close()
