import firebirdsql; from main import get_conn;
try:
    conn = get_conn('vulcano')
    cur = conn.cursor()
    cur.execute("SELECT FIRST 1 ID FROM USUARIO WHERE USUARIOID='CEOFERNANDO'")
    if not cur.fetchone():
        cur.execute("INSERT INTO USUARIO (USUARIOID, NOMECOMPLETO, EMAIL, SENHA, ATIVO, TIPOPERMISSAO) VALUES ('CEOFERNANDO', 'CEO Fernando', 'ceo@vulcano.com.br', 'direcao8829', 'T', 1)")
        conn.commit()
        print('Usuário inserido.')
    else:
        cur.execute("UPDATE USUARIO SET SENHA='direcao8829' WHERE USUARIOID='CEOFERNANDO'")
        conn.commit()
        print('Usuário atualizado.')
except Exception as e: print('Error:', e)
