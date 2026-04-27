import os, firebirdsql
from dotenv import load_dotenv
load_dotenv()
conn = firebirdsql.connect(
    host=os.environ.get('FIREBIRD_HOST','localhost'),
    database=os.environ.get('DB_PATH_VULCANO',''),
    user=os.environ.get('FIREBIRD_USER','SYSDBA'),
    password=os.environ.get('FIREBIRD_PASSWORD','masterkey'),
    charset='WIN1252'
)
cur = conn.cursor()
cur.execute("SELECT ID, NOME, METRAGEMTOTAL, OBRACONCLUIDA FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = 959 ORDER BY ID DESC")
print("ID   | CONCL | METRAGEM    | NOME")
print("-" * 75)
for r in cur.fetchall():
    nome = r[1].decode('win1252','ignore').strip() if isinstance(r[1], bytes) else str(r[1] or '')
    concl = str(r[3] or 'N')
    metro = float(r[2] or 0)
    print(f"{r[0]:4} | {concl:5} | {metro:>11.2f} | {nome[:40]}")
conn.close()
