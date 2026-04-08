import firebirdsql

DB_PATH_VULCANO = r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB"

try:
    conn = firebirdsql.connect(
        host="localhost",
        database=DB_PATH_VULCANO,
        port=3050,
        user="SYSDBA",
        password="masterkey",
        charset="WIN1252"
    )
    cur = conn.cursor()

    cur.execute("SELECT FIRST 5 ID, NOME, RET FROM EMPREENDIMENTO")
    print("EMPREENDIMENTO (RET):")
    for row in cur.fetchall():
        print(row)

    cur.execute('''
        SELECT FIRST 5 v.ID, v.TOTALVENDA, u.DESCRICAO
        FROM VENDA v
        LEFT JOIN UNIDADE u ON v.UNIDIMOB = u.ID
        WHERE v.TOTALVENDA IS NOT NULL
    ''')
    print("\nVENDA to UNIDADE:")
    for row in cur.fetchall():
        print(row)

    conn.close()
except Exception as e:
    print("Test ERR:", e)
