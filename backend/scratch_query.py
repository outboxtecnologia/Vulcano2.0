import fdb
import os
from dotenv import load_dotenv

load_dotenv()
con = fdb.connect(
    host=f"{os.getenv('FIREBIRD_HOST')}/{os.getenv('FIREBIRD_PORT')}",
    database=os.getenv('FIREBIRD_QUESTOR_PATH'),
    user=os.getenv('FIREBIRD_USER'),
    password=os.getenv('FIREBIRD_PASSWORD'),
    charset='ISO8859_1'
)
cur = con.cursor()

print('--- Validação LCTOCTB ---')
cur.execute('SELECT FIRST 20 CHAVELCTOCTB, CHAVEORIGEM, CODIGOORIGLCTOCTB FROM LCTOCTB WHERE CHAVEORIGEM IS NOT NULL')
for r in cur.fetchall():
    print('CHAVEORIGEM:', r)

cur.execute('SELECT FIRST 20 CHAVELCTOCTB, CHAVEORIGEM, CODIGOORIGLCTOCTB FROM LCTOCTB WHERE CODIGOORIGLCTOCTB IS NOT NULL')
print('\n--- Validação CODIGOORIGLCTOCTB ---')
for r in cur.fetchall():
    print('CODIGOORIGLCTOCTB:', r)

cur.execute('SELECT CODIGOORIGLCTOCTB, COUNT(*) FROM LCTOCTB GROUP BY 1 ORDER BY 2 DESC')
print('\n--- Agrupamento Códigos ---')
for r in cur.fetchall():
    print(r)
