import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import asyncio
from core.database.connection import get_conn

async def run():
    conn = get_conn('questor')
    cur = conn.cursor()
    cur.execute("SELECT CONTACTB, CLASSIFCTB, NOMEQUACONTAB FROM QUACONTAB WHERE CODIGOEMPRESA = 959 AND NOMEQUACONTAB LIKE '%DEPOSITO BANCARIO%'")
    for r in cur.fetchall():
        print(r)

asyncio.run(run())
