import firebirdsql

DB = r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB"

def main():
    conn = firebirdsql.connect(
        host="localhost",
        database=DB,
        port=3050,
        user="SYSDBA",
        password="masterkey",
        charset="WIN1252",
    )
    cur = conn.cursor()

    def cols(table: str):
        cur.execute(
            """
            SELECT TRIM(RDB$FIELD_NAME)
            FROM RDB$RELATION_FIELDS
            WHERE RDB$RELATION_NAME = ?
            ORDER BY RDB$FIELD_POSITION
            """,
            (table,),
        )
        return [r[0] for r in cur.fetchall()]

    for t in ["VENDA", "RECEBER", "VENDAFORMAPAGTO", "VENDAREPARCELAMENTO", "DISTRATO", "VENDAUNIDADE"]:
        try:
            c = cols(t)
            print(f"{t}: {len(c)} cols")
            print(" ", ", ".join(c[:80]))
        except Exception as e:
            print(f"{t}: ERROR {e}")

    cur.execute(
        """
        SELECT TRIM(r.RDB$RELATION_NAME)
        FROM RDB$RELATION_FIELDS f
        JOIN RDB$RELATIONS r ON r.RDB$RELATION_NAME = f.RDB$RELATION_NAME
        WHERE r.RDB$SYSTEM_FLAG=0 AND TRIM(f.RDB$FIELD_NAME)='IDVENDA'
        ORDER BY 1
        """
    )
    print("tables_with_IDVENDA:", [r[0] for r in cur.fetchall()])

    conn.close()

if __name__ == "__main__":
    main()

