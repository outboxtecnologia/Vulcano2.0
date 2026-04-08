import main
with open('distrato_cols.txt', 'w') as f:
    try:
        conn = main.get_conn('vulcano')
        cur = conn.cursor()
        cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'DISTRATO'")
        fields = [r[0].strip() for r in cur.fetchall()]
        f.write(f"DISTRATO columns: {fields}\n")
    except Exception as e:
        f.write(str(e))
