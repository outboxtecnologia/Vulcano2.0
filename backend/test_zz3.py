import firebirdsql
try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\.gemini\\antigravity\\scratch\\questor_mapping\\QUESTOR_EMPRESA_959.FDB')
    cur = conn.cursor()
    cur.execute("SELECT FIRST 10 CAST(CHAVEORIGEM AS VARCHAR(50)) FROM LCTOCTB WHERE CAST(CHAVEORIGEM AS VARCHAR(50)) STARTING WITH 'ZZ'")
    res = cur.fetchall()
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_zz_out.txt', 'w', encoding='utf-8').write('LCTOs ZZ: ' + str(res))
except Exception as e:
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_zz_out.txt', 'w', encoding='utf-8').write(str(e))
