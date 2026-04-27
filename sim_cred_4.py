import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import main
conn = main.get_conn('questor')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM LCTOGER WHERE CODIGOCENTROCUSTO = 35 AND NATURLCTOCTB = 2")
print("CC 35 Credit Count in LCTOGER:", cur.fetchone()[0])
conn.close()
