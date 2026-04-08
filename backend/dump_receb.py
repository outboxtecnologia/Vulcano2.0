import firebirdsql

conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB',
    user='SYSDBA',
    password='masterkey',
    charset='WIN1252'
)
cur = conn.cursor()

tbls = ["BAIXA_RECEBER", "RECEBIMENTO", "CONTA_RECEBER_BAIXA", "RECEBER_BAIXA", "TITULO_RECEBER", "TITULO_RECEBER_BAIXA"]

with open("receb_sys_utf8.txt", "w", encoding="utf-8") as f:
    for t in tbls:
        try:
            cur.execute(f"SELECT FIRST 1 * FROM {t}")
            f.write(f"{t} First Row: {cur.fetchone()}\\n")
        except Exception as e:
            f.write(f"{t} Erro: {e}\\n")
            
    try:
        cur.execute("SELECT FIRST 1 * FROM RECEBER WHERE TOTALPAGO IS NOT NULL AND TOTALPAGO > 0")
        f.write(f"RECEBER (T>0) First Row: {cur.fetchone()}\\n")
    except Exception as e:
        f.write(f"RECEBER (T>0) Erro: {e}\\n")

    try:
        cur.execute("SELECT FIRST 1 * FROM RECEBER WHERE VALORPARCELA IS NOT NULL AND VALORPARCELA > 0")
        f.write(f"RECEBER (V>0) First Row: {cur.fetchone()}\\n")
    except Exception as e:
        f.write(f"RECEBER (V>0) Erro: {e}\\n")

conn.close()
