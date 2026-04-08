import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.main import get_conn, get_receitas_caixa, api_contabilizacoes

ano = 2024
mes = 4
empresa_id = 959
empreendimento_id = "6400000000003"

res = api_contabilizacoes(ano=ano, mes=mes, empresa_id=empresa_id, empreendimento_id=empreendimento_id)

conn_v = get_conn("vulcano")
cur_v = conn_v.cursor()
cur_v.execute("SELECT ID, NOME, OBRACONCLUIDA, CONTACAIXA FROM EMPREENDIMENTO WHERE ID = ?", (empreendimento_id,))
emp = cur_v.fetchone()
print(f"Empreendimento: {emp}")

res_rec = get_receitas_caixa(empresa_id=empresa_id, data_ini=f"{ano}-{str(mes).zfill(2)}", data_fim=f"{ano}-{str(mes).zfill(2)}")
meta = res_rec.get("dashboard_meta", {}).get(emp[1] if emp else "Residencial Stuttgart")

if meta:
    print(f"Caixa_mes: {meta.get('CAIXA_MES')}")
    print(f"Trib: {meta.get('trib_detalhe_caixa_mes')}")
else:
    print("META NAO ENCONTRADO PARA O EMPREENDIMENTO")

cur_v.execute("SELECT PERIODO, PERCENTUAL FROM POC WHERE ID_EMPREENDIMENTO = ?", (empreendimento_id,))
print("POCs:", cur_v.fetchall())

try:
    cur_v.execute("SELECT SUM(CUSTO_TOTAL) FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ?", (empreendimento_id,))
    print("Custo Mensal Real total:", cur_v.fetchone())
except Exception as e:
    print("Erro POC_CUSTO:", e)
