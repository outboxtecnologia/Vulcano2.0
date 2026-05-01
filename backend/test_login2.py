import firebirdsql
try:
    conn = firebirdsql.connect(
        host='127.0.0.1', 
        port=3050, 
        database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\Vulcano 2025\VULCANO 2025.fdb', 
        user='SYSDBA', 
        password='masterkey', 
        charset='WIN1252'
    )
    cur = conn.cursor()
    cur.execute("SELECT EMAIL, SENHA FROM USUARIO WHERE ATIVO = 'T'")
    for r in cur.fetchall():
        print(f"Email: {r[0]}, Senha: {r[1]}")
    conn.close()
except Exception as e:
    print("ERRO FB:", e)
