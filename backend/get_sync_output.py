import sys
import json
from main import get_conn
try:
    c = get_conn('questor')
    cur = c.cursor()
    cur.execute("SELECT extract(year from lctoger.datalctoctb), extract(month from lctoger.datalctoctb), coalesce(sum(coalesce(lctoger.valorlctoger*lctoger.naturlctoctb, 0)), 0) FROM lctoger INNER JOIN lctoctb ON lctoctb.codigoempresa = lctoger.codigoempresa AND lctoctb.chavelctoctb = lctoger.chavelctoctb WHERE lctoger.codigoempresa = 959 AND lctoger.codigocentrocusto = 27 AND not (lctoctb.codigohistctb = 370 and lctoger.naturlctoctb = -1) GROUP BY 1, 2 ORDER BY 1 DESC, 2 DESC")
    res = [(int(row[0]), int(row[1]), float(row[2])) for row in cur.fetchall()]
    with open('sync_output.json', 'w') as f:
        json.dump(res, f)
except Exception as e:
    with open('sync_output.json', 'w') as f:
        f.write(str(e))
