import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn
import re

empreendimento_id = 959
empresa_id = 1 # or whatever
cc_empreendimento = 35

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT EXTRACT(YEAR FROM G.DATALCTOCTB), EXTRACT(MONTH FROM G.DATALCTOCTB), G.VALORLCTOGER, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), H.DESCRHISTCTB
      FROM LCTOGER G
      JOIN LCTOCTB C ON C.CHAVELCTOCTB = G.CHAVELCTOCTB AND C.CODIGOEMPRESA = G.CODIGOEMPRESA
      LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
      WHERE G.CODIGOCENTROCUSTO = ? AND G.NATURLCTOCTB = -1 AND G.DATALCTOCTB >= '2020-01-01'
  """, (cc_empreendimento,))
cr_rows = cur_q.fetchall()
creditos_agrupados = {}
for (v_ano, v_mes, v_val, h_compl, h_desc) in cr_rows:
    if isinstance(h_compl, (bytes, bytearray)):
        t_compl = h_compl.decode("cp1252", "ignore")
    elif hasattr(h_compl, "read"):
        t_compl = h_compl.read().decode("cp1252", "ignore")
    else:
        t_compl = str(h_compl or "")
    h_full = f"{str(h_desc or '')} {t_compl}".upper().replace('Ê', 'E').strip()
    if h_full.startswith('TRANSFERENCIA DE CUSTO'):
        k = f"{int(v_ano)}-{int(v_mes)}"
        creditos_agrupados[k] = creditos_agrupados.get(k, 0.0) + float(v_val or 0.0)

print(f"Agrupado em {len(creditos_agrupados.keys())} meses:")
for k, v in creditos_agrupados.items():
    print(f"Mês {k} => {v}")

