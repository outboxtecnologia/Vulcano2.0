"""
Investigação focada: conta 4995 (RET A RECOLHER) Stuttgart 04/2025
Usando campos corretos do Vulcano
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

conn_q = get_conn("questor")
conn_v = get_conn("vulcano")
cur_q = conn_q.cursor()
cur_v = conn_v.cursor()

print("CONTA 4995 = RET A RECOLHER (Retenção a Recolher — IRRF/PIS/COFINS retidos)")
print("Stuttgart = ID:335, CC:35, ContaCusto:5667, ContaEstand:5639")
print()

print("=" * 70)
print("A. Vendas Stuttgart com distrato/cancelamento")
print("=" * 70)
cur_v.execute("""
    SELECT v.ID, v.NUMCADIMOB, v.DESCUNIDIMOB, v.TOTALVENDA, v.DTOPER,
           v.DISTRATO, v.DATADISTRATO, v.CODIGOEMPRESA
    FROM VENDA v
    WHERE v.IDEMPREENDIMENTO = 335
    ORDER BY v.DESCUNIDIMOB
""")
vendas = cur_v.fetchall()
print(f"  Vendas Stuttgart: {len(vendas)}")
distratos_ativos = []
for v in vendas:
    distrato = dec(v[5])
    data_dist = v[6]
    marcador = ""
    if distrato and distrato.upper() == 'S':
        marcador = f" [DISTRATO dist={data_dist}]"
        if data_dist and str(data_dist)[:7] == '2025-04':
            distratos_ativos.append(v)
            marcador += " <<< ABRIL 2025"
    print(f"  ID:{v[0]} | {dec(v[2])} | R${v[3]:.2f} | {v[4]} | Distrato:{distrato}{marcador}")

print()
print("=" * 70)
print("B. LCTOCTB conta 4995 em 04/2025 (empresa 959) — lançamentos reais")
print("=" * 70)
cur_q.execute("""
    SELECT C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, C.VALORLCTOCTB,
           H.DESCRHISTCTB,
           CAST(C.COMPLHIST AS VARCHAR(200))
    FROM LCTOCTB C
    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
    WHERE C.CODIGOEMPRESA = 959
      AND (C.CONTACTBDEB = 4995 OR C.CONTACTBCRED = 4995)
      AND C.DATALCTOCTB >= CAST('2025-04-01' AS DATE)
      AND C.DATALCTOCTB  < CAST('2025-05-01' AS DATE)
    ORDER BY C.DATALCTOCTB, C.VALORLCTOCTB DESC
""")
rows = cur_q.fetchall()
total_deb = sum(r[3] for r in rows if r[1] == 4995)
total_cred = sum(r[3] for r in rows if r[2] == 4995)
print(f"  Lançamentos: {len(rows)} | Débito total: R${total_deb:.2f} | Crédito total: R${total_cred:.2f} | Líquido: R${total_deb-total_cred:.2f}")
for r in rows:
    nat = 'D' if r[1] == 4995 else 'C'
    print(f"  {r[0]} | {nat} | D:{r[1]} C:{r[2]} | R${r[3]:.2f} | {dec(r[4])} | {dec(r[5])[:70]}")

print()
print("=" * 70)
print("C. Motor VU2: impostos configurados com conta 4995")
print("=" * 70)
cur_v.execute("""
    SELECT ID, NOME, CONTA_DESP_IMP, CONTA_CRED_IMP_REC_DARF, ALIQUOTA_ISS,
           ALIQUOTA_PIS, ALIQUOTA_COFINS, ALIQUOTA_CSLL, ALIQUOTA_IRPJ
    FROM IMPOSTO
    WHERE CODIGOEMPRESA = 959
    ORDER BY ID
""")
impostos = cur_v.fetchall()
for imp in impostos:
    marcador = " <<< CONTA 4995" if (str(imp[2] or '') == '4995' or str(imp[3] or '') == '4995') else ""
    print(f"  ID:{imp[0]} | {dec(imp[1])} | ContaDesp:{imp[2]} | ContaRec:{imp[3]} | "
          f"ISS:{imp[4]}% PIS:{imp[5]}% COF:{imp[6]}% CSLL:{imp[7]}% IRPJ:{imp[8]}%{marcador}")

print()
print("=" * 70)
print("D. VU2 via API: contabilizações 04/2025 Stuttgart — contas com 4995")
print("=" * 70)
# Chama o api_saldo_contas que é síncrona, passando a conta 4995
from main import api_saldo_contas
result_fisico = api_saldo_contas(empresa_id=959, mes=4, ano=2025, contas='4995', empreendimento_id='335')
for conta in result_fisico.get('data', []):
    print(f"  Conta {conta['conta']} (QUESTOR) 04/2025:")
    print(f"    Saldo Ant: R${conta.get('saldo_anterior',0):.2f}")
    print(f"    Mov Deb:   R${conta.get('movimento_debito',0):.2f}")
    print(f"    Mov Cred:  R${conta.get('movimento_credito',0):.2f}")
    print(f"    Saldo Fin: R${conta.get('saldo_final',0):.2f}")
    print(f"    Detalhes ({len(conta.get('detalhes',[]))} lançamentos):")
    for det in conta.get('detalhes', []):
        print(f"      {det.get('data','')} | {det.get('natureza','')} | R${det.get('valor',0):.2f} | {det.get('historico','')[:80]}")

print()
print("=" * 70)
print("E. Verificação: qual a receita do Stuttgart e tributos esperados 04/2025")
print("=" * 70)
# Receita esperada = POC do período × VGV das vendas ativas × alíquota tributo
# Busca POC histórico
cur_v.execute("""
    SELECT COMPETENCIA, POC_PERCENTUAL, POC_PERCENTUAL_ANTERIOR
    FROM HISTORICO_POC
    WHERE EMPREENDIMENTO_ID = 335
    ORDER BY COMPETENCIA DESC
""")
poc_hist = cur_v.fetchall()
poc_abr = None
poc_mar = None
for p in poc_hist:
    comp = str(p[0])[:7]
    if comp == '2025-04' and poc_abr is None: poc_abr = p
    if comp == '2025-03' and poc_mar is None: poc_mar = p
print(f"  POC Abril/2025: {poc_abr[1] if poc_abr else 'N/A'}%  POC Anterior: {poc_abr[2] if poc_abr else 'N/A'}%")
print(f"  POC Março/2025: {poc_mar[1] if poc_mar else 'N/A'}%")
if poc_abr:
    delta_poc = float(poc_abr[1] or 0) - float(poc_abr[2] or 0)
    print(f"  Delta POC no mês: {delta_poc:.4f}%")
    # VGV ativo das vendas não distraídas
    vgv_ativo = sum(float(v[3]) for v in vendas if dec(v[5]).upper() != 'S')
    print(f"  VGV ativo (sem distratos): R${vgv_ativo:.2f}")
    receita_reconhecida = vgv_ativo * (delta_poc / 100.0)
    print(f"  Receita reconhecida estimada: R${receita_reconhecida:.2f}")
