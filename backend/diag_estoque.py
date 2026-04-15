"""
Diagnóstico: por que a conta 5639 (Stuttgart) não aparece na auditoria?
Verifica cada etapa do pipeline para identificar onde os valores se perdem.
"""
import firebirdsql, os, sys
from dotenv import load_dotenv
load_dotenv("backend/.env", override=True)

DB_Q = os.environ.get("DB_PATH_QUESTOR",  r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB")
DB_V = os.environ.get("DB_PATH_VULCANO",  r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\Vulcano 2025\VULCANO 2025.fdb")
HOST = os.environ.get("FIREBIRD_HOST", "localhost")
PORT = int(os.environ.get("FIREBIRD_PORT", "3050"))
USER = os.environ.get("FIREBIRD_USER", "SYSDBA")
PASS = os.environ.get("FIREBIRD_PASSWORD", "masterkey")
EMPRESA = 959

def conn(db): return firebirdsql.connect(host=HOST, port=PORT, database=db,
                                          user=USER, password=PASS, charset="WIN1252")

cv = conn(DB_V)
cq = conn(DB_Q)

print("=" * 60)
print("1. CADASTRO DOS EMPREENDIMENTOS ATIVOS (Vulcano)")
print("=" * 60)
cur = cv.cursor()
cur.execute("""
    SELECT ID, NOME, CODIGOCENTROCUSTO, CONTAESTAND, CONTAESTCON,
           CONTACUSTO, OBRACONCLUIDA, ATIVO
    FROM EMPREENDIMENTO
    WHERE CODIGOEMPRESA = ? AND ATIVO = 'S'
    ORDER BY ID
""", (EMPRESA,))
emps = cur.fetchall()
for r in emps:
    print(f"""
  ID={r[0]} | {str(r[1] or '').strip()[:40]}
    CC={r[2]} | CONTAESTAND={r[3]} | CONTAESTCON={r[4]}
    CONTACUSTO={r[5]} | OBRACONCLUIDA={r[6]} | ATIVO={r[7]}""")

print()
print("=" * 60)
print("2. SIMULANDO LÓGICA DO PIPELINE para cada empreendimento:")
print("   custo_gasto_anterior e custo_gasto_vigente do LCTOGER/CC")
print("=" * 60)

# Mês alvo de teste: Março/2025
ANO, MES = 2025, 3
data_inicio = f"{ANO}-{str(MES).zfill(2)}-01"
data_fim    = f"{ANO}-{str(MES+1).zfill(2)}-01" if MES < 12 else f"{ANO+1}-01-01"

for r in emps:
    id_emp, nome, cc, conta_estand, conta_estcon, conta_custo, ob_conc, _ = r
    nome = str(nome or '').strip()
    ob_concluida = str(ob_conc or 'N').strip().upper() == 'S'
    c_estoque_raw = conta_estcon if ob_concluida else conta_estand
    c_estoque = int(c_estoque_raw) if c_estoque_raw else None

    print(f"\n  [{id_emp}] {nome[:35]}")
    print(f"    CC={cc} | c_estoque={c_estoque} | ob_concluida={ob_concluida}")

    if not cc:
        print(f"    ⚠️  SEM CC → empreendimento ignorado pelo pipeline!")
        continue

    cq2 = cq.cursor()
    cq2.execute("""
        SELECT
          SUM(CASE WHEN C.DATALCTOCTB < CAST(? AS DATE)
                   THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_anterior,
          SUM(CASE WHEN C.DATALCTOCTB < CAST(? AS DATE)
                   THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_vigente
        FROM LCTOGER G
        JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                      AND C.CHAVELCTOCTB  = G.CHAVELCTOCTB
        WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ?
          AND C.DATALCTOCTB < CAST(? AS DATE)
          AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
          AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
    """, (data_inicio, data_fim, EMPRESA, int(cc), data_fim))
    row = cq2.fetchone()
    ant = float(row[0] or 0.0)
    vig = float(row[1] or 0.0)
    mov = vig - ant

    print(f"    custo_anterior={ant:,.2f} | custo_vigente={vig:,.2f} | mov_mes={mov:,.2f}")

    # Simular a condição do inject:
    if abs(mov) > 0.01 or abs(ant) > 0.01:
        print(f"    ✅  inject_virtual_entry SERIA chamado → conta {c_estoque}, valor={abs(mov):,.2f}, saldo_ant={ant:,.2f}")
    else:
        print(f"    ❌  inject_virtual_entry NÃO seria chamado (mov={mov:.2f}, ant={ant:.2f})")

    if not c_estoque:
        print(f"    ⚠️  c_estoque=None → inject ignorado mesmo com valores!")

cv.close()
cq.close()
print()
print("=" * 60)
print("CONCLUSÃO: verificar acima os empreendimentos com ❌ ou ⚠️")
print("=" * 60)
