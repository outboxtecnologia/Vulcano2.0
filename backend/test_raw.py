from main import get_conn
import pandas as pd
conn = get_conn("vulcano")
query = """
SELECT 
    v.CODIGOEMPRESA,
    v.CODIGOESTAB,
    e.NOME AS EMPREENDIMENTO,
    v.UNIDIMOB AS UNIDADE,
    r.DATA AS DATA_RECEBIMENTO,
    r.TOTALPAGO AS RECEITA_CAIXA
FROM VENDA v
JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
LEFT JOIN RECEBER r ON r.IDVENDA = v.ID AND r.TOTALPAGO > 0
WHERE e.NOME LIKE '%STUTTGART%' AND r.DATA >= '2024-04-01' AND r.DATA <= '2024-04-30'
"""
df = pd.read_sql(query, conn)
print("DF para Stuttgart em Abril/2024:")
print(df)
