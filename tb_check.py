import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn
conn_v = get_conn()
cur_v = conn_v.cursor()

cur_v.execute('select id_empreendimento, nome from EMPREENDIMENTO where nome like ''%STUTT%''')
emp = cur_v.fetchone()
print(emp)
emp_id = emp[0]

cur_v.execute('select id_unidade, descricao, metragem from UNIDADE where id_empreendimento = ?', (emp_id,))
unidades = cur_v.fetchall()
for u in unidades[:5]:
    print(u)
