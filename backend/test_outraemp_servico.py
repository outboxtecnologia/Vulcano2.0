import firebirdsql
from main import get_conn

try:
    conn = get_conn('questor')
    cur = conn.cursor()
    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'OUTRAEMPPGTOSERVICO'")
    print('Fields:', [r[0].strip() for r in cur.fetchall()])
    cur.execute("SELECT COUNT(*) FROM OUTRAEMPPGTOSERVICO WHERE CODIGOEMPRESA = 959")
    print('Count:', cur.fetchone()[0])
    cur.execute("SELECT FIRST 5 * FROM OUTRAEMPPGTOSERVICO WHERE CODIGOEMPRESA = 959 AND VALORSERVICO > 0")
    print('Sample:', cur.fetchall())
except Exception as e:
    print('Error:', e)
