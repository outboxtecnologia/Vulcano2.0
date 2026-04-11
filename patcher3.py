with open('backend/vector_sync.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the Questor query to remove COMPLHIST but keep DESCRHISTCTB
sql_old = """    cur.execute(\"\"\"
        SELECT C.CHAVELCTOCTB, C.DATALCTOCTB, C.VALORLCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, 
           C.COMPLHIST as desc,
           C.CODIGOORIGLCTOCTB,
           H.DESCRHISTCTB
    FROM LCTOCTB C
    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
    WHERE C.CODIGOEMPRESA = ?
          AND EXTRACT(YEAR FROM C.DATALCTOCTB) = 2025
          AND EXTRACT(MONTH FROM C.DATALCTOCTB) IN (5, 6)
          AND C.CODIGOORIGLCTOCTB <> 'ZZ'
    \"\"\", (empresa_id,))"""

sql_new = """    cur.execute(\"\"\"
        SELECT C.CHAVELCTOCTB, C.DATALCTOCTB, C.VALORLCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, 
           '' as desc,
           C.CODIGOORIGLCTOCTB,
           H.DESCRHISTCTB
    FROM LCTOCTB C
    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
    WHERE C.CODIGOEMPRESA = ?
          AND EXTRACT(YEAR FROM C.DATALCTOCTB) = 2025
          AND EXTRACT(MONTH FROM C.DATALCTOCTB) IN (5, 6)
          AND C.CODIGOORIGLCTOCTB <> 'ZZ'
    \"\"\", (empresa_id,))"""

text = text.replace(sql_old, sql_new)

with open('backend/vector_sync.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Removed COMPLHIST from query")
