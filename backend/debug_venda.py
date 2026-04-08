import firebirdsql
import sys

try:
    c = firebirdsql.connect(
        host='localhost',
        database='C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB',
        port=3050,
        user='SYSDBA',
        password='masterkey'
    ).cursor()
    
    # 1. Check CLIENTE columns just in case
    c.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLIENTE'")
    print("CLIENTE columns:", [r[0].strip() for r in c.fetchall()])
    
    # 2. Check VENDA counts
    c.execute("SELECT COUNT(*) FROM VENDA WHERE CODIGOEMPRESA = 959")
    print("Vendas emp 959:", c.fetchone()[0])
    
    # 3. Check DISTRATO values
    c.execute("SELECT DISTRATO, COUNT(*) FROM VENDA WHERE CODIGOEMPRESA = 959 GROUP BY 1")
    print("DISTRATO emp 959:", c.fetchall())
        
    c.execute("SELECT ID_CLIENTE, COUNT(*) FROM VENDA WHERE CODIGOEMPRESA = 959 GROUP BY 1")
    print("Has ID_CLIENTE?", len(c.fetchall()) > 0)
    
except Exception as e:
    print("Erro:", e)
