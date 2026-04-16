import sys, os
sys.path.insert(0, os.path.abspath('.'))
import firebirdsql, dotenv
dotenv.load_dotenv('../.env')
try:
    conn = firebirdsql.connect(
        host=os.environ.get('FB_HOST', 'localhost'),
        database=os.environ.get('FB_DB'),
        port=int(os.environ.get('FB_PORT', 3050)),
        user=os.environ.get('FB_USER', 'SYSDBA'),
        password=os.environ.get('FB_PASSWORD', 'masterkey'),
        charset='WIN1252'
    )
    cur = conn.cursor()
    cur.execute("SELECT CONTACTB, CLASSIFCTB, NOMEQUACONTAB FROM QUACONTAB WHERE CODIGOEMPRESA = 959 AND NOMEQUACONTAB LIKE '%DEPOSIT%'")
    for row in cur.fetchall(): print(row)
except Exception as e:
    print('Erro', e)
