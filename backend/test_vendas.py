from main import get_conn
import json
c = get_conn('vulcano').cursor()
c.execute("SELECT DISTINCT EMPREENDIMENTO FROM VENDAS WHERE EMPREENDIMENTO LIKE '%STUTT%'")
print("Empreendimentos em VENDAS:", c.fetchall())
