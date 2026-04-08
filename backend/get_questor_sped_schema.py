import firebirdsql
import json

target_tables = [
    'EFDUNIDIMOBILIARIA',
    'EFDUNIDIMOBVENDIDA',
    'EFDINCORPIMOBRET',
    'EFDAJUSTEPISCOFINS',
    'EFDAJUSTEPISCOFINSDET'
]

questor_db = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB"

out = {}
try:
    conn = firebirdsql.connect(
        host="localhost",
        database=questor_db,
        port=3050,
        user="SYSDBA",
        password="masterkey",
        charset="WIN1252"
    )
    cur = conn.cursor()
    
    for table in target_tables:
        cur.execute("""
            SELECT RDB$FIELD_NAME 
            FROM RDB$RELATION_FIELDS 
            WHERE RDB$RELATION_NAME = ?
            ORDER BY RDB$FIELD_POSITION
        """, (table,))
        cols = [r[0].strip() for r in cur.fetchall()]
        out[table] = cols
        
    with open("questor_sped_schema.json", "w") as f:
        json.dump(out, f, indent=2)
except Exception as e:
    print("Error:", e)
