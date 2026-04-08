import firebirdsql
import sys
try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB')
    cur = conn.cursor()
    out = ""
    for t in ['FECHAMENTO', 'POC_CUSTO_MENSAL_REAL', 'EMPREENDIMENTO']:
        try:
            cur.execute(f"SELECT FIRST 1 * FROM {t}")
            desc = [d[0] for d in cur.description]
            out += f"Cols of {t}: {desc}\n"
        except:
            pass
    open('c:/Users/dirfe/.gemini/antigravity/scratch/vulcano2.0/backend/test_custo_out.txt', 'w', encoding='utf-8').write(out)
except Exception as e:
    open('c:/Users/dirfe/.gemini/antigravity/scratch/vulcano2.0/backend/test_custo_out.txt', 'w', encoding='utf-8').write(str(e))
