"""Diagnóstico das tabelas Questor usadas pelo endpoint SERO/INSS."""
import firebirdsql, os
from dotenv import load_dotenv
load_dotenv()

Q_HOST = os.environ.get('FIREBIRD_HOST', 'localhost')
Q_USER = os.environ.get('FIREBIRD_USER', 'SYSDBA')
Q_PASS = os.environ.get('FIREBIRD_PASSWORD', 'masterkey')
Q_DB   = os.environ.get('DB_PATH_QUESTOR', '')

EMPRESA_ID = 959

conn = firebirdsql.connect(host=Q_HOST, database=Q_DB, user=Q_USER, password=Q_PASS, charset='WIN1252')
cur  = conn.cursor()

# 1. CALCULORATEIO — colunas
cur.execute("""SELECT TRIM(RDB$FIELD_NAME) FROM RDB$RELATION_FIELDS
               WHERE RDB$RELATION_NAME='CALCULORATEIO' ORDER BY RDB$FIELD_POSITION""")
print("CALCULORATEIO cols:", [r[0] for r in cur.fetchall()])

# 2. PERIODOCALCULO — colunas
cur.execute("""SELECT TRIM(RDB$FIELD_NAME) FROM RDB$RELATION_FIELDS
               WHERE RDB$RELATION_NAME='PERIODOCALCULO' ORDER BY RDB$FIELD_POSITION""")
print("PERIODOCALCULO cols:", [r[0] for r in cur.fetchall()])

# 3. OUTRAEMPRESA — colunas
cur.execute("""SELECT TRIM(RDB$FIELD_NAME) FROM RDB$RELATION_FIELDS
               WHERE RDB$RELATION_NAME='OUTRAEMPRESA' ORDER BY RDB$FIELD_POSITION""")
print("OUTRAEMPRESA cols:", [r[0] for r in cur.fetchall()])

# 4. OUTRAEMPEMP — colunas
cur.execute("""SELECT TRIM(RDB$FIELD_NAME) FROM RDB$RELATION_FIELDS
               WHERE RDB$RELATION_NAME='OUTRAEMPEMP' ORDER BY RDB$FIELD_POSITION""")
print("OUTRAEMPEMP cols:", [r[0] for r in cur.fetchall()])

# 5. TERCEIROPGTO — colunas
cur.execute("""SELECT TRIM(RDB$FIELD_NAME) FROM RDB$RELATION_FIELDS
               WHERE RDB$RELATION_NAME='TERCEIROPGTO' ORDER BY RDB$FIELD_POSITION""")
print("TERCEIROPGTO cols:", [r[0] for r in cur.fetchall()])

# 6. Amostra CALCULORATEIO evento 5041
print("\n--- AMOSTRA CALCULORATEIO (evento 5041, empresa 959) ---")
cur.execute("""
    SELECT FIRST 10 C.CODIGOOUTEMP, C.CODIGOPERCALCULO, SUM(C.VALOREVENTO)
    FROM CALCULORATEIO C
    WHERE C.CODIGOEVENTO = 5041 AND C.CODIGOEMPRESA = ?
    GROUP BY C.CODIGOOUTEMP, C.CODIGOPERCALCULO
    ORDER BY C.CODIGOPERCALCULO DESC
""", (EMPRESA_ID,))
rows = cur.fetchall()
for r in rows:
    print(f"  OUTEMP={r[0]}, PERCALC={r[1]}, VALOR={r[2]}")

if rows:
    # 7. Competência via PERIODOCALCULO
    sample_perc = rows[0][1]
    cur.execute("SELECT COMPET FROM PERIODOCALCULO WHERE CODIGOPERCALCULO = ?", (sample_perc,))
    compet_row = cur.fetchone()
    print(f"\nCOMPET para CODIGOPERCALCULO={sample_perc}: {compet_row}")

    # 8. OUTRAEMPRESA para o primeiro OUTEMP
    sample_outemp = rows[0][0]
    cur.execute("""
        SELECT OE.CODIGOOUTEMP, OE.NOMEOUTEMP, OE.INSCRFEDERAL
        FROM OUTRAEMPRESA OE WHERE OE.CODIGOOUTEMP = ?
    """, (sample_outemp,))
    oe = cur.fetchone()
    print(f"OUTRAEMPRESA para OUTEMP={sample_outemp}: {oe}")

# 9. Amostra TERCEIROPGTO
print("\n--- AMOSTRA TERCEIROPGTO (empresa 959) ---")
cur.execute("""SELECT TRIM(RDB$FIELD_NAME) FROM RDB$RELATION_FIELDS
               WHERE RDB$RELATION_NAME='TERCEIROPGTO' ORDER BY RDB$FIELD_POSITION""")
cols_t = [r[0] for r in cur.fetchall()]
print("  Colunas:", cols_t)
try:
    cur.execute("SELECT FIRST 5 * FROM TERCEIROPGTO WHERE CODIGOEMPRESA = ?", (EMPRESA_ID,))
    t_rows = cur.fetchall()
    for r in t_rows:
        print("  ", dict(zip(cols_t, r)))
except Exception as e:
    print("  Erro TERCEIROPGTO:", e)

conn.close()
