import firebirdsql
try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB')
    cur = conn.cursor()
    cur.execute("SELECT FIRST 5 * FROM POC_CUSTOS")
    rows = cur.fetchall()
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_custo_out.txt', 'w', encoding='utf-8').write("POC_CUSTOS:\n" + str(rows))
except Exception as e:
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_custo_out.txt', 'w', encoding='utf-8').write(str(e))
