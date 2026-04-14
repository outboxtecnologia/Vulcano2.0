import fdb

def main():
    conn = fdb.connect(dsn='127.0.0.1:3050:C:\\Projetos\\Firebird\\Questor.fdb', user='SYSDBA', password='masterkey')
    cur = conn.cursor()
    
    query = """
        SELECT FIRST 10 DATA, VALOR, ID_EMPREENDIMENTO, ID_CONTA_DEBITO, ID_CONTA_CREDITO
        FROM LANCAMENTO_CONTABIL
        WHERE (ID_CONTA_DEBITO = 5653 OR ID_CONTA_CREDITO = 5653)
    """
    cur.execute(query)
    rows = cur.fetchall()
    print(f"Rows for 5653: {len(rows)}")
    for r in rows:
        print(r)
        
    conn.close()

if __name__ == "__main__":
    main()
