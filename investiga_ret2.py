"""
RET distrato — parte 2: dados do IMPOSTO config + recebimentos distratados + ciclo de contas
"""
import sys
sys.path.insert(0, 'backend')
from main import get_conn

def dec(v):
    if v is None: return ''
    try:
        if hasattr(v, 'read'): return v.read().decode('cp1252', 'ignore')
        return v.decode('latin-1') if isinstance(v, bytes) else str(v)
    except: return str(v)
def fmt(v): return f"R${float(v or 0):,.2f}"

conn_q = get_conn("questor")
conn_v = get_conn("vulcano")
cur_q = conn_q.cursor()
cur_v = conn_v.cursor()

print("=" * 70)
print("A. Configuração IMPOSTO RET — Stuttgart empresa 959")
print("=" * 70)
cur_v.execute("SELECT FIRST 10 * FROM IMPOSTO")
cols = [dec(d[0]) for d in cur_v.description]
rows = cur_v.fetchall()
for r in rows:
    d = {cols[i]: (dec(r[i]) if isinstance(r[i], (bytes, bytearray)) else r[i]) for i in range(len(cols))}
    print(f"\n  ID:{d['ID']} | {d['DESCRICAO']}")
    print(f"    RET:{d['RET']} | ALIQUOTA:{d['ALIQUOTA']}")
    print(f"    CONTA_DEB_IMP_SOBRE_VENDA:     {d['CONTA_DEB_IMP_SOBRE_VENDA']}")
    print(f"    CONTA_CRED_IMP_REC_PASSIVO_SOC:{d['CONTA_CRED_IMP_REC_PASSIVO_SOC']}")
    print(f"    CONTA_DEB_IMP_REC_PASSIVO_SOC: {d['CONTA_DEB_IMP_REC_PASSIVO_SOC']}")
    print(f"    CONTA_DEB_IMP_APROP_ATIVO:     {d['CONTA_DEB_IMP_APROP_ATIVO']}")
    print(f"    CONTA_CRED_IMP_REC_DARF:       {d['CONTA_CRED_IMP_REC_DARF']}")

print()
print("=" * 70)
print("B. Tabela RET_IMPOSTO_MENSAL ou CTB_IMPOSTOS_MENSAL — acumulados por empreendimento")
print("=" * 70)
cur_v.execute("SELECT FIRST 1 * FROM CTB_IMPOSTOS_MENSAL")
cols_ctb = [dec(d[0]) for d in cur_v.description]
print(f"  Colunas CTB_IMPOSTOS_MENSAL: {cols_ctb}")

# Dados Stuttgart 2025
cur_v.execute("""
    SELECT FIRST 20 * FROM CTB_IMPOSTOS_MENSAL
    WHERE EMPREENDIMENTO_ID = 335
    ORDER BY ANO DESC, MES DESC
""")
rows_ctb = cur_v.fetchall()
print(f"  Registros Stuttgart (ID=335): {len(rows_ctb)}")
for r in rows_ctb:
    d = {cols_ctb[i]: r[i] for i in range(len(cols_ctb))}
    print(f"  {d}")

print()
print("=" * 70)
print("C. Recebimentos (caixa) históricos das vendas 333 e 334")
print("   Na VENDA: campo TOTALVENDA, DTOPER; recebimentos em PARCELAS?")
print("=" * 70)
# Verifica tabelas de parcelas/recebimentos
for t in ['PARCELAVENDA', 'PARCELA', 'RECEBIMENTO', 'VENDA_PARCELA', 'VENDAUNIDADE']:
    try:
        cur_v.execute(f"SELECT FIRST 1 * FROM {t}")
        cols_t = [dec(d[0]) for d in cur_v.description]
        print(f"  {t}: {cols_t[:10]}")
    except:
        pass

# Busca recebimentos nas vendas 333 e 334 diretamente
# PARCELAVENDA é o mais comum nos sistemas imobiliários
try:
    cur_v.execute("""
        SELECT p.* FROM PARCELAVENDA p
        WHERE p.ID_VENDA IN (16829, 16831)
        ORDER BY p.DATA_VENCIMENTO NULLS LAST
    """)
    cols_p = [dec(d[0]) for d in cur_v.description]
    rows_p = cur_v.fetchall()
    print(f"\n  PARCELAVENDA vendas 333/334: {len(rows_p)} parcelas")
    total_rec = 0.0
    for r in rows_p[:30]:
        d = {cols_p[i]: r[i] for i in range(len(cols_p))}
        pago = float(d.get('VALOR_PAGO', d.get('VALORPAGO', 0)) or 0)
        total_rec += pago
        print(f"  {d}")
    print(f"\n  TOTAL recebido APTO 1602+1603: {fmt(total_rec)}")
    print(f"  RET 4% = {fmt(total_rec * 0.04)}")
except Exception as e:
    print(f"  Erro PARCELAVENDA: {e}")

print()
print("=" * 70)
print("D. Plano de contas Questor — contas vizinhas da 4995 faixa 4900-5000")
print("=" * 70)
cur_q.execute("""
    SELECT CONTACTB, DESCRCONTA FROM PLANOESPEC
    WHERE CODIGOEMPRESA = 959 AND CONTACTB BETWEEN 4900 AND 5010
    ORDER BY CONTACTB
""")
for r in cur_q.fetchall():
    marcador = " <<< RET" if r[0] == 4995 else ""
    print(f"  Conta {r[0]}: {dec(r[1])}{marcador}")

print()
print("=" * 70)
print("E. LCTOCTB completo 2025 conta 4995 — entendimento do ciclo")
print("=" * 70)
cur_q.execute("""
    SELECT C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, C.VALORLCTOCTB,
           H.DESCRHISTCTB, CAST(C.COMPLHIST AS VARCHAR(200))
    FROM LCTOCTB C
    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
    WHERE C.CODIGOEMPRESA = 959
      AND (C.CONTACTBDEB = 4995 OR C.CONTACTBCRED = 4995)
      AND C.DATALCTOCTB >= CAST('2025-01-01' AS DATE)
    ORDER BY C.DATALCTOCTB
""")
rows_all = cur_q.fetchall()
saldo = 0.0
print(f"  Total lançamentos 4995 em 2025: {len(rows_all)}")
for r in rows_all:
    nat = 'D' if r[1] == 4995 else 'C'
    v = float(r[3])
    saldo += v if nat == 'D' else -v
    print(f"  {str(r[0])[:10]} | {nat} | D:{r[1]} C:{r[2]} | {fmt(v)} | saldo_acum={fmt(saldo)} | {dec(r[4])} | {dec(r[5])[:60]}")

print()
print("=" * 70)
print("F. Como o VU2 calcula tributos — função no graph_logic_builder")
print("=" * 70)
# Procura no código como os tributos são calculados
try:
    with open('backend/core/services/graph_logic_builder.py', 'r', encoding='utf-8') as f:
        src = f.read()
    # Procura seção de tributos/imposto/RET
    import re
    # Encontra funções/blocos com RET ou imposto
    matches = [(m.start(), src[m.start():m.start()+600]) for m in re.finditer(r'(ret|imposto|tributo|aliquota)', src, re.IGNORECASE)]
    print(f"  Menções a RET/imposto/tributo no builder: {len(matches)}")
    for start, txt in matches[:3]:
        line_no = src[:start].count('\n') + 1
        print(f"\n  --- Linha ~{line_no} ---")
        print(txt[:500])
except Exception as e:
    print(f"  Erro: {e}")
