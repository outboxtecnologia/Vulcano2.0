import json
import sqlite3
import os
import sys

# We need to query FIREBIRD, so use furi
sys.path.append(os.path.abspath("backend"))
from backend.core.services.database import get_vulcano_db

try:
    conn = get_vulcano_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT FIRST 20 DATA, VALOR, ID_EMPREENDIMENTO, ID_CONTA_DEBITO, ID_CONTA_CREDITO, HISTORICO
        FROM LANCAMENTO_CONTABIL
        WHERE (ID_CONTA_DEBITO = 5653 OR ID_CONTA_CREDITO = 5653 OR ID_CONTA_DEBITO=5667 OR ID_CONTA_CREDITO=5667)
          AND DATA >= CAST('2025-11-01' AS DATE) AND DATA < CAST('2025-12-01' AS DATE)
    ''')
    for row in cur.fetchall():
        print(row)
except Exception as e:
    import traceback
    traceback.print_exc()
