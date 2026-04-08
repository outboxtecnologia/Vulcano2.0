import firebirdsql
import sys
try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB')
    cur = conn.cursor()
    # Check if there is a table for CUSTOS or FECHAMENTO
    cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME LIKE '%CUSTO%' OR RDB$RELATION_NAME LIKE '%FECHAMENTO%'")
    tables = cur.fetchall()
    
    out = "Tables:\n" + str(tables) + "\n\n"
    
    if len(tables) > 0:
        table_name = tables[0][0].strip()
        cur.execute(f"SELECT FIRST 1 * FROM {table_name}")
        desc = [d[0] for d in cur.description]
        out += f"Cols of {table_name}: {desc}\n"
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_custo_out.txt', 'w', encoding='utf-8').write(out)
except Exception as e:
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_custo_out.txt', 'w', encoding='utf-8').write(str(e))
