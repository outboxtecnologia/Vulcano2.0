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
      SELECT EXTRACT(YEAR FROM G.DATALCTOCTB), 
             EXTRACT(MONTH FROM G.DATALCTOCTB), 
             G.VALORLCTOGER,
             CAST(C.COMPLHIST AS BLOB SUB_TYPE 0) AS COMPLHIST,
             H.DESCRHISTCTB
      FROM LCTOGER G
      JOIN LCTOCTB C ON C.CHAVELCTOCTB = G.CHAVELCTOCTB AND C.CODIGOEMPRESA = G.CODIGOEMPRESA
      LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
      WHERE G.CODIGOCENTROCUSTO = ? AND G.NATURLCTOCTB = -1 AND G.DATALCTOCTB >= '2020-01-01'
  """, (cc_empreendimento,))
cr_rows = cur_q.fetchall()
creditos_detalhados = []
for (ano_c, mes_c, val_c, c_hist, d_hist) in cr_rows:
    if isinstance(c_hist, (bytes, bytearray)):
        compl_lc = c_hist.decode("cp1252", "ignore")
    elif hasattr(c_hist, "read"):
        compl_lc = c_hist.read().decode("cp1252", "ignore")
    else:
        compl_lc = str(c_hist or "")
    texto_completo = f"{str(d_hist or '')} {compl_lc}".upper()
    if 'TRANSFER' in texto_completo and 'CUSTO' in texto_completo:
        creditos_detalhados.append({
            "ano": int(ano_c), "mes": int(mes_c), 
            "valor": float(val_c or 0), 
            "historico": texto_completo
        })
        print(texto_completo)

print(f"Found {len(creditos_detalhados)} specific credit transfers for CC 35!")
