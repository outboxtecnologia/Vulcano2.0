import sys
print("Carregando modulo main...")
import main
conn = main.get_conn('vulcano')
cur = conn.cursor()
try:
    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'EMPREENDIMENTO'")
    fields = [r[0].strip() for r in cur.fetchall()]
    print("Found CNO?", 'CNO' in fields)
    if 'CNO' not in fields:
        print("Adicionando CNO...")
        cur.execute("ALTER TABLE EMPREENDIMENTO ADD CNO VARCHAR(30)")
        conn.commit()
    else:
        print("CNO ja existe")
finally:
    conn.close()
print("Successo")
