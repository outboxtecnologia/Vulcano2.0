import firebirdsql
import datetime

DB_PATH_VULCANO = r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB"
conn = firebirdsql.connect(
    host="localhost",
    database=DB_PATH_VULCANO,
    port=3050,
    user="SYSDBA",
    password="masterkey",
    charset="WIN1252"
)
cur = conn.cursor()
try:
    cur.execute("""
            SELECT r.DATA, r.TOTALPAGO, r.VALORPARCELA, r.VALORVARIACAO, v.DESCUNIDIMOB, c.CNPJ, r.PARCELA, c.NOME, e.NOME, r.OBS
            FROM RECEBER r
            JOIN VENDA v ON r.IDVENDA = v.ID
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE v.CODIGOEMPRESA = ?
            ORDER BY r.DATA DESC
    """, (959,))
    rows = cur.fetchall()

    def dec(v):
        if v is None: return ""
        if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
        return str(v).strip()

    receb = []
    for r in rows:
        receb.append({
            "data": r[0].strftime('%Y-%m-%d') if hasattr(r[0], 'strftime') else dec(r[0]), 
            "total_pago": float(r[1] or 0), 
            "valor_parcela": float(r[2] or 0), 
            "variacao": float(r[3] or 0), 
            "unidade": dec(r[4]), 
            "cliente_cnpj": dec(r[5]), 
            "parcela": dec(r[6]), 
            "cliente_nome": dec(r[7]), 
            "empreendimento": dec(r[8]),
            "obs": dec(r[9])
        })
    print("Parsed successfully:", len(receb))
except Exception as e:
    print("ERROR:", str(e))
finally:
    conn.close()
