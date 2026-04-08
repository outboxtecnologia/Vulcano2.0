import firebirdsql
try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\.gemini\\antigravity\\scratch\\questor_mapping\\QUESTOR_EMPRESA_959.FDB')
    cur = conn.cursor()
    # Let's search inside CODIGOORIGLCTOCTB, ORIGEMDADO, CODIGOLCTOPROG, NUMERODCTO, or anything
    q = "SELECT FIRST 10 CHAVEORIGEM, ORIGEMDADO, CODIGOORIGLCTOCTB, COMPLHIST, DESCRCONTACTBDEB, DATALCTOCTB FROM LCTOCTB WHERE EXTRACT(MONTH FROM DATALCTOCTB) = 12 AND EXTRACT(DAY FROM DATALCTOCTB) = 31 AND VALORLCTOCTB > 0"
    cur.execute(q)
    res = cur.fetchall()
    with open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_zz_out.txt', 'w', encoding='utf-8') as f:
        f.write('LCTOs 12/31:\n')
        for r in res: f.write(str(r) + '\n')
except Exception as e:
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_zz_out.txt', 'w', encoding='utf-8').write(str(e))
