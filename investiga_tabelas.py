import sys
sys.path.insert(0, 'backend')
from main import get_conn

def dec(v):
    if v is None: return ''
    try: return v.decode('latin-1') if isinstance(v, bytes) else str(v)
    except: return str(v)

conn_q = get_conn("questor")
cur = conn_q.cursor()

# Tabelas do Questor com "CONTA" ou "PLANO"
cur.execute("SELECT rdb$relation_name FROM rdb$relations WHERE rdb$system_flag=0 AND rdb$relation_type=0 ORDER BY 1")
tables = [dec(r[0]).strip() for r in cur.fetchall()]
conta_tables = [t for t in tables if 'CONTA' in t or 'PLANO' in t]
print("Tabelas relacionadas a contas:", conta_tables[:20])
