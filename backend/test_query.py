import firebirdsql

conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB',
    user='SYSDBA',
    password='masterkey',
    charset='WIN1252'
)
cur = conn.cursor()

try:
    query = """
    SELECT FIRST 10
        v.CODIGOEMPRESA,
        v.CODIGOESTAB,
        e.NOME AS EMPREENDIMENTO,
        v.UNIDIMOB AS UNIDADE,
        c.NOME AS COMPRADOR,
        r.DATA AS DATA_RECEBIMENTO,
        r.TOTALPAGO AS RECEITA_CAIXA,
        v.VALORVENDA AS VGV
    FROM VENDA v
    JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
    LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
    LEFT JOIN RECEBER r ON r.IDVENDA = v.ID AND r.TOTALPAGO > 0
    WHERE v.SITUACAO = 1 AND v.CODIGOEMPRESA = 959
    """
    cur.execute(query)
    print("Sucesso!")
    for row in cur.fetchall():
        print(row)
        
except Exception as e:
    print("Erro na query:", e)
finally:
    conn.close()
