import firebirdsql
import json
try:
    c = firebirdsql.connect(
        host='localhost',
        database='C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB',
        port=3050,
        user='SYSDBA',
        password='masterkey'
    ).cursor()
    c.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'RECEBER'")
    cols = sorted([r[0].strip() for r in c.fetchall()])
    
    out = {"columns": cols, "payments_>0": [], "all_payments": []}
    
    c.execute("SELECT EXTRACT(YEAR FROM DATA), SUM(TOTALPAGO) FROM RECEBER WHERE TOTALPAGO > 0 GROUP BY 1")
    for row in c.fetchall():
        out["payments_>0"].append({ "year": row[0], "sum": row[1] })
        
    c.execute("SELECT EXTRACT(YEAR FROM DATA), SUM(TOTALPAGO) FROM RECEBER GROUP BY 1")
    for row in c.fetchall():
        out["all_payments"].append({ "year": row[0], "sum": row[1] })
        
    with open("check_receber.json", "w") as f:
        json.dump(out, f, indent=2)
except Exception as e:
    print(e)
