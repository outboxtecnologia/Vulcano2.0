import firebirdsql
try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB')
    cur = conn.cursor()
    cur.execute("SELECT FIRST 1 * FROM EMPREENDIMENTO")
    desc = [d[0] for d in cur.description]
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_custo_out.txt', 'w', encoding='utf-8').write("EMPREENDIMENTO: " + str(desc))
except Exception as e:
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_custo_out.txt', 'w', encoding='utf-8').write(str(e))
