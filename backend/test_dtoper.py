import sys
sys.path.append(r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend')
from main import get_conn
import pandas as pd
conn=get_conn('vulcano')
print(pd.read_sql_query('SELECT FIRST 1 DTOPER FROM VENDA', conn))
conn.close()
