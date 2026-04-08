import sys
sys.path.append('backend')
from main import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()

try:
    cur.execute("SELECT FIRST 1 * FROM EMPREENDIMENTO")
    columns = [desc[0] for desc in cur.description]
    print("Columns in EMPREENDIMENTO:")
    for col in columns:
        print(col)
except Exception as e:
    import traceback
    traceback.print_exc()
