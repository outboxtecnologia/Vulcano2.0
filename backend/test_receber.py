from main import get_conn
conn = get_conn('vulcano')
c = conn.cursor()
c.execute("""
SELECT e.NOME, r.DATA, r.TOTALPAGO 
FROM VENDA v 
JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID 
JOIN RECEBER r ON r.IDVENDA = v.ID 
WHERE e.NOME LIKE '%STUTTG%'\n""")
res = c.fetchall()
print("STUTTGART RECEBIMENTOS:")
for r in res[:10]:
    print(r)
