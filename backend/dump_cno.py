import firebirdsql
import json

def get_conn():
    return firebirdsql.connect(
        host='localhost',
        port=3050,
        database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB',
        user='SYSDBA',
        password='masterkey',
        charset='WIN1252'
    )

try:
    conn = get_conn()
    cur = conn.cursor()
    meta = {}
    for table in ['OUTRAEMPRESA', 'CALCULORATEIO', 'PERIODOCALCULO']:
        try:
            cur.execute(f"SELECT FIRST 1 * FROM {table}")
            cols = [d[0] for d in cur.description]
            meta[table] = cols
        except Exception as e:
            meta[table] = str(e)

    print(json.dumps(meta, indent=2))
except Exception as e:
    print(f"Error connecting: {e}")
