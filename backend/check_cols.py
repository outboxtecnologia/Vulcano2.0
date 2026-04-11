import main
conn = main.get_conn('vulcano')
cur = conn.cursor()
cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'VENDA'")
print("VENDA:", [r[0].strip() for r in cur.fetchall()])
cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'EMPREENDIMENTO'")
print("EMPREENDIMENTO:", [r[0].strip() for r in cur.fetchall()])
