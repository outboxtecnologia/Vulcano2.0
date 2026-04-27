import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import cub_agent
from main import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()

import calendar
for comp, val in cub_agent.HISTORICO_BASE.items():
    ano, mes = map(int, comp.split("-"))
    last_day = calendar.monthrange(ano, mes)[1]
    data_db = f"{ano}-{mes:02d}-{last_day}"
    
    cur.execute("SELECT MES FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND MES = ?", (data_db,))
    existia = cur.fetchone()
    if existia:
        cur.execute("UPDATE INDICE_REAJUSTE_TABELA SET PERCENTUAL_VARIACAO = ?, VALOR = ? WHERE ID_INDICE_REAJUSTE = 1 AND MES = ?", (val, val, data_db))
    else:
        cur.execute("INSERT INTO INDICE_REAJUSTE_TABELA (ID_INDICE_REAJUSTE, MES, VALOR, PERCENTUAL_VARIACAO) VALUES (1, ?, ?, ?)", (data_db, val, val))
conn.commit()
conn.close()
print("Historical CUB Injected!!!")
