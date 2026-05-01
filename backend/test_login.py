import main
try:
    conn = main.get_conn("vulcano")
    cur = conn.cursor()
    cur.execute("SELECT EMAIL, SENHA FROM USUARIO WHERE ATIVO = 'T'")
    rows = cur.fetchall()
    print("Usuarios Ativos:")
    for r in rows:
        print(f"Email: {r[0]}, Senha: {r[1]}")
except Exception as e:
    print("Erro:", e)
