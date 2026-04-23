"""
Diagnóstico: gap entre VENDAFORMAPAGTOPRAZO (projetado) e RECEBER (efetivo)
Objetivo: entender o "quebra-cabeça" das parcelas quitadas vs. em aberto.
"""
import firebirdsql
import json
from datetime import date

DB_PATH = r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB"

conn = firebirdsql.connect(
    host="localhost", database=DB_PATH,
    port=3050, user="SYSDBA", password="masterkey", charset="WIN1252"
)
cur = conn.cursor()

print("=" * 70)
print("1. CONTAGENS GERAIS")
print("=" * 70)

cur.execute("SELECT COUNT(*) FROM VENDAFORMAPAGTO WHERE ATIVA = 'S'")
vfp_ativas = cur.fetchone()[0]
print(f"  VENDAFORMAPAGTO (ATIVA=S):           {vfp_ativas}")

cur.execute("SELECT COUNT(*) FROM VENDAFORMAPAGTOPRAZO")
vfpp_total = cur.fetchone()[0]
print(f"  VENDAFORMAPAGTOPRAZO total:          {vfpp_total}")

cur.execute("SELECT COUNT(*) FROM VENDAFORMAPAGTOPRAZO WHERE VALOR_PAGO > 0")
vfpp_pagas = cur.fetchone()[0]
print(f"  VENDAFORMAPAGTOPRAZO VALOR_PAGO>0:   {vfpp_pagas}")

cur.execute("SELECT COUNT(*) FROM VENDAFORMAPAGTOPRAZO WHERE VALOR_PAGO = 0 OR VALOR_PAGO IS NULL")
vfpp_abertas = cur.fetchone()[0]
print(f"  VENDAFORMAPAGTOPRAZO abertas (=0):   {vfpp_abertas}")

cur.execute("SELECT COUNT(*) FROM RECEBER")
rec_total = cur.fetchone()[0]
print(f"  RECEBER total:                       {rec_total}")

cur.execute("SELECT COUNT(*) FROM RECEBER WHERE TOTALPAGO > 0")
rec_pagas = cur.fetchone()[0]
print(f"  RECEBER TOTALPAGO>0 (quitadas):      {rec_pagas}")

cur.execute("SELECT COUNT(*) FROM RECEBER WHERE TOTALPAGO = 0 OR TOTALPAGO IS NULL")
rec_abertas = cur.fetchone()[0]
print(f"  RECEBER TOTALPAGO=0 (em aberto):     {rec_abertas}")

print()
print("=" * 70)
print("2. COBERTURA: quantas parcelas do PRAZO tem ID na RECEBER")
print("=" * 70)

cur.execute("""
    SELECT COUNT(*)
    FROM VENDAFORMAPAGTOPRAZO vpp
    WHERE EXISTS (
        SELECT 1 FROM RECEBER r
        WHERE r.IDVENDAFORMAPAGTOPRAZO = vpp.ID
    )
""")
com_receber = cur.fetchone()[0]
print(f"  VENDAFORMAPAGTOPRAZO COM registro em RECEBER:  {com_receber}")

cur.execute("""
    SELECT COUNT(*)
    FROM VENDAFORMAPAGTOPRAZO vpp
    WHERE NOT EXISTS (
        SELECT 1 FROM RECEBER r
        WHERE r.IDVENDAFORMAPAGTOPRAZO = vpp.ID
    )
""")
sem_receber = cur.fetchone()[0]
print(f"  VENDAFORMAPAGTOPRAZO SEM registro em RECEBER:  {sem_receber}  <-- GAP candidatas a em aberto")

print()
print("=" * 70)
print("3. AMOSTRA: 10 parcelas SEM RECEBER (orfas = candidatas a aberto)")
print("=" * 70)

cur.execute("""
    SELECT
        vpp.ID        AS prazo_id,
        vpp.DATA      AS vencimento,
        vpp.VALOR     AS valor_projetado,
        vpp.VALOR_PAGO,
        vpp.REFERENCIA,
        vfp.ID        AS formapagto_id,
        vfp.DESCRICAO AS descricao_forma,
        vfp.IDVENDA,
        v.CODIGOEMPRESA,
        v.UNIDIMOB,
        v.ID_CLIENTE
    FROM VENDAFORMAPAGTOPRAZO vpp
    JOIN VENDAFORMAPAGTO vfp ON vfp.ID = vpp.IDVENDAFORMAPAGTO
    JOIN VENDA v ON v.ID = vfp.IDVENDA
    WHERE NOT EXISTS (
        SELECT 1 FROM RECEBER r WHERE r.IDVENDAFORMAPAGTOPRAZO = vpp.ID
    )
    AND vfp.ATIVA = 'S'
    AND (v.DISTRATO IS NULL OR v.DISTRATO = '')
    ORDER BY vpp.DATA
    ROWS 1 TO 10
""")
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("  Colunas:", cols)
for row in rows:
    print(" ", dict(zip(cols, row)))

print()
print("=" * 70)
print("4. AMOSTRA: 5 registros RECEBER existentes (referencia de estrutura)")
print("=" * 70)

cur.execute("""
    SELECT r.ID, r.IDVENDA, r.IDCLIENTE, r.DATA, r.VALORPARCELA,
           r.VALORVARIACAO, r.TOTALPAGO, r.PARCELA, r.OBS,
           r.IDVENDAFORMAPAGTO, r.DESCONTO, r.IDVENDAFORMAPAGTOPRAZO
    FROM RECEBER r
    ROWS 1 TO 5
""")
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("  Colunas:", cols)
for row in rows:
    print(" ", dict(zip(cols, row)))

print()
print("=" * 70)
print("5. PARCELAS ABERTAS (VALOR_PAGO=0) sem RECEBER por empresa")
print("=" * 70)

cur.execute("""
    SELECT v.CODIGOEMPRESA, COUNT(*) as qtd, SUM(vpp.VALOR) as valor_total
    FROM VENDAFORMAPAGTOPRAZO vpp
    JOIN VENDAFORMAPAGTO vfp ON vfp.ID = vpp.IDVENDAFORMAPAGTO
    JOIN VENDA v ON v.ID = vfp.IDVENDA
    WHERE NOT EXISTS (
        SELECT 1 FROM RECEBER r WHERE r.IDVENDAFORMAPAGTOPRAZO = vpp.ID
    )
    AND (vpp.VALOR_PAGO = 0 OR vpp.VALOR_PAGO IS NULL)
    AND vfp.ATIVA = 'S'
    AND (v.DISTRATO IS NULL OR v.DISTRATO = '')
    GROUP BY v.CODIGOEMPRESA
    ORDER BY valor_total DESC
""")
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
for row in rows:
    print(" ", dict(zip(cols, row)))

print()
print("=" * 70)
print("6. DISTRATO - verificar valores distintos")
print("=" * 70)
cur.execute("SELECT DISTINCT DISTRATO FROM VENDA WHERE DISTRATO IS NOT NULL ROWS 1 TO 5")
rows = cur.fetchall()
print("  Valores de DISTRATO:", [r[0] for r in rows])

print()
print("=" * 70)
print("7. MAX ID atual de RECEBER (para gerar novos IDs)")
print("=" * 70)
cur.execute("SELECT MAX(ID) FROM RECEBER")
max_id = cur.fetchone()[0]
print(f"  MAX(ID) em RECEBER: {max_id}")

print()
print("=" * 70)
print("8. VERIFICAR: parcelas pagas (VALOR_PAGO>0) que nao tem RECEBER")
print("=" * 70)
cur.execute("""
    SELECT COUNT(*)
    FROM VENDAFORMAPAGTOPRAZO vpp
    WHERE vpp.VALOR_PAGO > 0
    AND NOT EXISTS (
        SELECT 1 FROM RECEBER r WHERE r.IDVENDAFORMAPAGTOPRAZO = vpp.ID
    )
""")
pagas_sem_rec = cur.fetchone()[0]
print(f"  Parcelas pagas SEM registro em RECEBER: {pagas_sem_rec}")

conn.close()
print("\nDiagnostico concluido.")
