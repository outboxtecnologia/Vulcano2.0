import firebirdsql

DB_Q = r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB'
con = firebirdsql.connect(host='localhost', port=3050, database=DB_Q, user='SYSDBA', password='masterkey', charset='WIN1252')
cur = con.cursor()

def dec(v):
    if v is None: return ''
    if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
    return str(v).strip()

print("=" * 120)
print("LCTOGER Stuttgart | CC 35 | Empresa 959 | 03/2025 | 10 primeiros lancamentos analiticos")
print("=" * 120)

cur.execute("""
    SELECT FIRST 10
        lctoger.datalctoctb,
        lctoger.valorlctoger,
        lctoger.naturlctoctb,
        lctoger.valorlctoger * lctoger.naturlctoctb as valor_liquido,
        lctoger.contactb,
        lctoctb.contactbdeb,
        lctoctb.contactbcred,
        lctoctb.codigohistctb,
        lctoctb.complhist,
        lctoger.chavelctoctb
    FROM lctoger
    INNER JOIN lctoctb ON lctoctb.codigoempresa = lctoger.codigoempresa
        AND lctoctb.chavelctoctb = lctoger.chavelctoctb
    WHERE lctoger.codigoempresa = 959
      AND lctoger.codigocentrocusto = 35
      AND extract(year from lctoger.datalctoctb) = 2025
      AND extract(month from lctoger.datalctoctb) = 3
      AND NOT (lctoctb.codigohistctb = 370 AND lctoger.naturlctoctb = -1)
    ORDER BY lctoger.datalctoctb, lctoger.chavelctoctb
""")
rows = cur.fetchall()

print(f"{'DATA':<12} {'V_LIQUIDO':>14} {'CT_CC':>8} {'DEB':>6} {'CRED':>6} {'HISTCD':>6} | HISTORICO")
print('-' * 120)
for r in rows:
    data = str(r[0])[:10] if r[0] else '??'
    vliq = float(r[3] or 0)
    ct_cc = str(r[4] or '')
    ctdeb = str(r[5] or '')
    ctcred = str(r[6] or '')
    histcod = str(r[7] or '')
    hist = dec(r[8])[:50]
    print(f"{data:<12} {vliq:>14.2f} {ct_cc:>8} {ctdeb:>6} {ctcred:>6} {histcod:>6} | {hist}")

print()

# Totalizador mensal
cur.execute("""
    SELECT coalesce(sum(coalesce(lctoger.valorlctoger*lctoger.naturlctoctb,0)),0), count(*)
    FROM lctoger
    INNER JOIN lctoctb ON lctoctb.codigoempresa = lctoger.codigoempresa
        AND lctoctb.chavelctoctb = lctoger.chavelctoctb
    WHERE lctoger.codigoempresa = 959
      AND lctoger.codigocentrocusto = 35
      AND extract(year from lctoger.datalctoctb) = 2025
      AND extract(month from lctoger.datalctoctb) = 3
      AND NOT (lctoctb.codigohistctb = 370 AND lctoger.naturlctoctb = -1)
""")
tot = cur.fetchone()
print(f">>> TOTAL LIQUIDO 03/2025 CC35:  R$ {float(tot[0] if tot and tot[0] else 0):>14,.2f}")
print(f">>> TOTAL LANCAMENTOS NO MES:    {tot[1]}")

# Agora mostra como seria injetado no POC_CUSTO_MENSAL_REAL (query de sincronizacao)
print()
print("=" * 120)
print("QUERY DE SINCRONIZACAO (como e injetado em POC_CUSTO_MENSAL_REAL)")
print("=" * 120)
cur.execute("""
    SELECT
        extract(year from lctoger.datalctoctb) as ANO,
        extract(month from lctoger.datalctoctb) as MES,
        coalesce(sum(coalesce(lctoger.valorlctoger*lctoger.naturlctoctb,0)),0) as CUSTO_TOTAL
    FROM lctoger
    INNER JOIN lctoctb ON lctoctb.codigoempresa = lctoger.codigoempresa
        AND lctoctb.chavelctoctb = lctoger.chavelctoctb
    WHERE lctoger.codigoempresa = 959
      AND lctoger.codigocentrocusto = 35
      AND NOT (lctoctb.codigohistctb = 370 AND lctoger.naturlctoctb = -1)
    GROUP BY 1, 2
    ORDER BY 1 DESC, 2 DESC
""")
rows_tot = cur.fetchall()
print(f"{'ANO':<6} {'MES':<4} {'CUSTO_TOTAL':>16}  => INSERT INTO POC_CUSTO_MENSAL_REAL")
print('-' * 80)
for i, r in enumerate(rows_tot[:12]):
    ano = int(r[0])
    mes = int(r[1])
    val = float(r[2] or 0)
    comp = f"{ano}-{str(mes).zfill(2)}"
    marker = "  <<< 03/2025" if (ano == 2025 and mes == 3) else ""
    print(f"{ano:<6} {mes:<4} {val:>16,.2f}  competencia='{comp}'{marker}")

con.close()
print("\nOK")
