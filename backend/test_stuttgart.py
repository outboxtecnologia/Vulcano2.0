import firebirdsql

conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB',
    port=3050, user='SYSDBA', password='masterkey', charset='WIN1252'
)
cur = conn.cursor()

def decode(x):
    return x.decode('win1252').strip() if isinstance(x, bytes) else x

cur.execute("SELECT NUMCADIMOB, IDENTEMP FROM EFDUNIDIMOBILIARIA")
rows = cur.fetchall()
unidades = [r for r in rows if r[1] and ("STUT" in decode(r[1]).upper() or "STU" in decode(r[1]).upper())]
print('Unidades STUTTGART no Cadastro:', len(unidades))
if unidades:
    print('Exemplo ID:', unidades[0][0], decode(unidades[0][1]))
    ids = [r[0] for r in unidades]
    ids_str = ",".join(map(str, ids))
    if ids_str:
        try:
            cur.execute(f"SELECT COUNT(*) FROM EFDUNIDIMOBVENDIDA WHERE NUMCADIMOB IN ({ids_str})")
            count = cur.fetchone()[0]
            print('Vendas registradas no EFDUNIDIMOBVENDIDA:', count)
            if count > 0:
                cur.execute(f"SELECT VLTOTVEND FROM EFDUNIDIMOBVENDIDA WHERE NUMCADIMOB IN ({ids_str})")
                print('Amostra de VGV:', cur.fetchone())
        except Exception as e:
            print("Erro ao consultar vendas:", e)
