"""
Investigação RET distrato Stuttgart 04/2025:
- Levanta recebimentos históricos das vendas 333 (APTO 1602) e 334 (APTO 1603)
- Calcula 4% (RET) sobre o total recebido → valor a debitar em 4995
- Identifica conta de crédito (Tributos Antecipados vs Resultado RET)
- Verifica como o VU2 calcula o RET atual
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

print("=" * 70)
print("1. Configuração RET — impostos/tributos Stuttgart (empresa 959)")
print("=" * 70)
# Busca configuração de IMPOSTO no Vulcano
cur_v.execute("""
    SELECT FIRST 20 rdb$relation_name FROM rdb$relations
    WHERE rdb$system_flag = 0 AND rdb$relation_type = 0
    AND rdb$relation_name LIKE '%IMP%'
    ORDER BY 1
""")
print("  Tabelas de imposto:", [dec(r[0]).strip() for r in cur_v.fetchall()])

# Verifica estrutura da tabela IMPOSTO
cur_v.execute("SELECT FIRST 1 * FROM IMPOSTO")
cols_imp = [dec(d[0]) for d in cur_v.description]
print(f"  Colunas IMPOSTO: {cols_imp}")

# Dados do imposto RET Stuttgart
cur_v.execute("""
    SELECT * FROM IMPOSTO LIMIT 10
""")
# Não funciona com LIMIT no firebird, usa FIRST
try:
    cur_v.execute("SELECT FIRST 10 * FROM IMPOSTO")
    rows = cur_v.fetchall()
    for r in rows:
        vals = {cols_imp[i]: (dec(r[i]) if isinstance(r[i], bytes) else r[i]) for i in range(len(cols_imp))}
        print(f"  {vals}")
except Exception as e:
    print(f"  Erro IMPOSTO: {e}")

print()
print("=" * 70)
print("2. Recebimentos históricos — APTO 1602 (venda 333) e APTO 1603 (venda 334)")
print("   IDs Stuttgart empreendimento = 335, vendas 333 e 334")
print("=" * 70)

# No Vulcano, recebimentos ficam em PARCELA / RECEBIMENTO ou similar
# Verificar as tabelas de recebimento
cur_v.execute("""
    SELECT FIRST 20 rdb$relation_name FROM rdb$relations
    WHERE rdb$system_flag = 0 AND rdb$relation_type = 0
    AND (rdb$relation_name LIKE '%PARCEL%'
      OR rdb$relation_name LIKE '%RECEB%'
      OR rdb$relation_name LIKE '%PAGAM%'
      OR rdb$relation_name LIKE '%CAIXA%')
    ORDER BY 1
""")
print("  Tabelas de recebimento:", [dec(r[0]).strip() for r in cur_v.fetchall()])

# Verifica tabela PARCELAVENDA ou similar
for tabela in ['PARCELAVENDA', 'RECEBIMENTO', 'PARCELAS', 'PARCELAMENTO', 'VENDAPARCELA']:
    try:
        cur_v.execute(f"SELECT FIRST 1 * FROM {tabela}")
        cols = [dec(d[0]) for d in cur_v.description]
        print(f"  Tabela {tabela} existe — colunas: {cols[:8]}")
    except Exception as e:
        print(f"  {tabela}: não existe")

print()
print("=" * 70)
print("3. Como o VU2 calcula get_receitas_caixa para Stuttgart?")
print("   Vamos ver o total de caixa acumulado das vendas 333 e 334")
print("=" * 70)
# Chama o módulo de receitas de caixa diretamente
try:
    from core.services.revenue_time_pipeline import RevenueTimePipeline
    resultado = RevenueTimePipeline.get_receitas_caixa(
        conn_vulcano=conn_v,
        conn_questor=conn_q,
        empresa_id=959,
        ano=2025,
        mes=4
    )
    print(f"  Retornou {len(resultado)} itens")
    # Filtra Stuttgart
    for rec in resultado:
        nome = str(rec.get('nome_empreendimento', '') or rec.get('empreendimento', '') or '')
        if 'STUTT' in nome.upper() or rec.get('empreendimento_id') == 335:
            print(f"  {nome}: recebimento_caixa={rec.get('receita_caixa', rec.get('total_recebido', rec.get('caixa')))}")
            print(f"    Todas as chaves: {list(rec.keys())}")
            print(f"    Valores: {rec}")
except Exception as e:
    print(f"  Erro ao chamar get_receitas_caixa: {e}")
    import traceback; traceback.print_exc()

print()
print("=" * 70)
print("4. LCTOCTB — todos os lançamentos da conta 4995 em 2025 para empresa 959")
print("   (Para mapeamento completo do ciclo RET)")
print("=" * 70)
cur_q.execute("""
    SELECT C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, C.VALORLCTOCTB,
           H.DESCRHISTCTB, CAST(C.COMPLHIST AS VARCHAR(200))
    FROM LCTOCTB C
    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
    WHERE C.CODIGOEMPRESA = 959
      AND (C.CONTACTBDEB = 4995 OR C.CONTACTBCRED = 4995)
      AND C.DATALCTOCTB >= CAST('2025-01-01' AS DATE)
      AND C.DATALCTOCTB  < CAST('2026-01-01' AS DATE)
    ORDER BY C.DATALCTOCTB
""")
rows_ret = cur_q.fetchall()
print(f"  Lançamentos RET 2025: {len(rows_ret)}")
for r in rows_ret:
    nat = 'D' if r[1] == 4995 else 'C'
    print(f"  {r[0]} | {nat} | D:{r[1]} C:{r[2]} | R${r[3]:.2f} | {dec(r[4])} | {dec(r[5])[:80]}")

print()
print("=" * 70)
print("5. Conta D nos créditos do RET — o que é a conta crédito parceira 4958?")
print("=" * 70)
cur_q.execute("SELECT CONTACTB, DESCRCONTA FROM PLANOESPEC WHERE CODIGOEMPRESA = 959 AND CONTACTB IN (4958, 4910, 4845, 4995, 4996, 4997, 4998)")
for r in cur_q.fetchall():
    print(f"  Conta {r[0]}: {dec(r[1])}")
