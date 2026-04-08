import sys
sys.path.append('backend')
from main import get_conn
conn = get_conn('vulcano')
cur = conn.cursor()
cur.execute("SELECT CNO, METRAGEMTOTAL, DATAINICIORET, DATACONCLUSAO FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = 959")
rows = cur.fetchall()
res = []
for r in rows:
    cno = r[0].decode('win1252', 'ignore').strip() if isinstance(r[0], bytes) else str(r[0] or "").strip()
    res.append({"cno": cno, "met": float(r[1] or 0), "ini": str(r[2]), "fim": str(r[3])})
import json
with open('../cno_dates.json', 'w') as f:
    json.dump(res, f)
