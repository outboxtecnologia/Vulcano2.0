import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.main import get_conn

conn_v = get_conn("vulcano")
cur_v = conn_v.cursor()
empresa_id = 959
emp_id = 6400000000003

print("Running EMPREENDIMENTO query...")
cur_v.execute("SELECT ID, NOME, CODIGOCENTROCUSTO, CONTACUSTO, CONTACLI, CONTAADICLI, CONTACAIXA, CONTAESTAND, CONTAESTCON, OBRACONCLUIDA FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ? AND ATIVO = 'S' AND ID = ?", (empresa_id, emp_id))
print(cur_v.fetchall())

print("Running POC query...")
cur_v.execute("SELECT PERIODO, PERCENTUAL FROM POC WHERE ID_EMPREENDIMENTO = ?", (emp_id,))
print(cur_v.fetchall())

print("Running POC_CUSTO_MENSAL_REAL...")
cur_v.execute("SELECT SUM(CUSTO_TOTAL) FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ?", (emp_id,))
print(cur_v.fetchall())
