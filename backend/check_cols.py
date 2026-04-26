import firebirdsql

conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\Vulcano 2025\VULCANO 2025.fdb',
    user='SYSDBA',
    password='masterkey',
    charset='WIN1252'
)

cur = conn.cursor()
cur.execute("""
    SELECT TRIM(RDB$FIELD_NAME)
    FROM RDB$RELATION_FIELDS
    WHERE RDB$RELATION_NAME = 'EMPREENDIMENTO'
    ORDER BY RDB$FIELD_POSITION
""")
cols = [r[0] for r in cur.fetchall()]
print("Colunas da tabela EMPREENDIMENTO:")
for c in cols:
    print(" -", c)

# Verifica se tem CNO
tem_cno = 'CNO' in cols
print(f"\nTem coluna CNO? {tem_cno}")

# Testa a query simplificada
print("\nTestando query com ID, NOME, CNO (se existir):")
try:
    cur.execute("SELECT FIRST 5 ID, NOME FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = 959")
    rows = cur.fetchall()
    for r in rows:
        nome = r[1].decode('win1252', 'ignore').strip() if isinstance(r[1], bytes) else str(r[1]).strip()
        print(f"  ID={r[0]}, NOME={nome}")
except Exception as e:
    print(f"  Erro: {e}")

conn.close()
