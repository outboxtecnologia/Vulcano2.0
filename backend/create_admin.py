import firebirdsql
conn = firebirdsql.connect(
    host='localhost', 
    port=3050, 
    database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\Vulcano 2025\VULCANO 2025.fdb', 
    user='SYSDBA', 
    password='masterkey', 
    charset='WIN1252'
)
cur = conn.cursor()
try:
    cur.execute("INSERT INTO USUARIO (USUARIOID, NOMECOMPLETO, TIPOPERMISSAO, EMAIL, SENHA, ATIVO) VALUES ('admin', 'Administrador', 'ADMIN', 'admin@vulcano.com.br', '123456', 'T')")
    conn.commit()
    print('User created')
except Exception as e:
    print('Error:', e)
