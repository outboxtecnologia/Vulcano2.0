"""Sincroniza as parcelas projetadas (VENDAFORMAPAGTOPRAZO) para o SQLite.

Substitui o uso manual de scratch/sync_abertas.py: a tabela
parcelas_abertas_projetadas e criada pelo bootstrap_schema.py e populada
aqui (full replace). Sem essa carga, a tela de Recebimentos mostra apenas
as parcelas efetivas da RECEBER.
"""
import sqlite3


def sync_parcelas_projetadas(get_conn, poc_db_path):
    """Recalcula parcelas_abertas_projetadas a partir do Firebird (vulcano).

    get_conn: factory de conexao do main.py (get_conn('vulcano')).
    Retorna o total de parcelas em aberto gravadas.
    """
    conn_fb = get_conn("vulcano")
    try:
        cur_fb = conn_fb.cursor()

        cur_fb.execute(
            "SELECT IDVENDAFORMAPAGTOPRAZO FROM RECEBER WHERE IDVENDAFORMAPAGTOPRAZO IS NOT NULL"
        )
        efetivados = {r[0] for r in cur_fb.fetchall()}

        cur_fb.execute("""
            SELECT
                p.ID AS prazo_id,
                p.DATA AS data_venc,
                p.VALOR AS valor,
                p.REFERENCIA AS parcela_ref,
                f.ID AS forma_pagto_id,
                f.IDVENDA AS venda_id,
                v.ID_CLIENTE AS cliente_id,
                c.NOME AS cliente_nome,
                u.DESCRICAO AS unidade_descricao,
                b.IDEMPREENDIMENTO AS empreendimento_id
            FROM VENDAFORMAPAGTOPRAZO p
            JOIN VENDAFORMAPAGTO f ON f.ID = p.IDVENDAFORMAPAGTO
            JOIN VENDA v ON v.ID = f.IDVENDA
            JOIN CLIENTE c ON c.ID = v.ID_CLIENTE
            LEFT JOIN VENDAUNIDADE vu ON vu.IDVENDA = v.ID
            LEFT JOIN UNIDADE u ON u.ID = vu.IDUNIDADE
            LEFT JOIN BLOCO b ON b.ID = u.IDBLOCO
        """)
        projetadas = cur_fb.fetchall()
    finally:
        conn_fb.close()

    # Deduplica por prazo_id (multiplas unidades por venda) e descarta efetivadas.
    abertas = {}
    for p in projetadas:
        if p[0] not in efetivados:
            abertas[p[0]] = p
    abertas = list(abertas.values())

    conn_sq = get_conn("sqlite")
    try:
        cur_sq = conn_sq.cursor()
        cur_sq.execute("""
            CREATE TABLE IF NOT EXISTS parcelas_abertas_projetadas (
                prazo_id INTEGER PRIMARY KEY,
                data_venc TEXT,
                valor REAL,
                parcela_ref TEXT,
                forma_pagto_id INTEGER,
                venda_id INTEGER,
                cliente_id INTEGER,
                cliente_nome TEXT,
                unidade_descricao TEXT,
                empreendimento_id INTEGER
            )
        """)
        cur_sq.execute("DELETE FROM parcelas_abertas_projetadas")
        cur_sq.executemany("""
            INSERT INTO parcelas_abertas_projetadas (
                prazo_id, data_venc, valor, parcela_ref, forma_pagto_id,
                venda_id, cliente_id, cliente_nome, unidade_descricao, empreendimento_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(
            p[0],
            p[1].strftime("%Y-%m-%d") if hasattr(p[1], "strftime") else str(p[1]),
            float(p[2] or 0),
            str(p[3] or ""),
            p[4], p[5], p[6],
            str(p[7] or ""),
            str(p[8] or ""),
            p[9],
        ) for p in abertas])
        conn_sq.commit()
    finally:
        conn_sq.close()

    return len(abertas)
