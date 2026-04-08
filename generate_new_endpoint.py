import codecs

new_func = r'''@app.get("/api/receitas-caixa")
def get_receitas_caixa(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None):
    # Pandas Vectorized Engine Start
    import pandas as pd
    import numpy as np
    import collections
    import datetime
    
    conn = get_conn("vulcano")
    cur = conn.cursor()

    query = """
    SELECT 
        v.CODIGOEMPRESA,
        v.CODIGOESTAB,
        e.NOME AS EMPREENDIMENTO,
        v.UNIDIMOB AS UNIDADE,
        c.NOME AS COMPRADOR,
        r.DATA AS DATA_RECEBIMENTO,
        r.TOTALPAGO AS RECEITA_CAIXA,
        r.VALORPARCELA,
        r.VALORVARIACAO,
        v.TOTALVENDA AS VGV_BASE,
        e.RET,
        v.DISTRATO,
        v.DATADISTRATO,
        v.ID AS IDVENDA
    FROM VENDA v
    JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
    LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
    LEFT JOIN RECEBER r ON r.IDVENDA = v.ID AND r.TOTALPAGO > 0
    """
    
    try:
        conditions = []
        params = []
        if empresa_id is not None:
            conditions.append("v.CODIGOEMPRESA = ?")
            params.append(int(empresa_id))
        
        join_conditions = ""
        if data_fim:
            join_conditions = " AND r.DATA <= ?"
            params.insert(0, data_fim)
            
        query = query.replace("AND r.TOTALPAGO > 0", "AND r.TOTALPAGO > 0" + join_conditions)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        # Não precisamos de ORDER BY no SQL pois o Pandas cuidará das agregações, limitando carga do DB
        # Mas mantemos para equivalência.
        query += " ORDER BY r.DATA DESC NULLS LAST"
        
        df = pd.read_sql_query(query, conn, params=tuple(params))
        
        # Saneamento Vetorizável
        df['EMPREENDIMENTO'] = df['EMPREENDIMENTO'].fillna('').astype(str).str.strip()
        
        def safe_decode(x):
            if isinstance(x, bytes):
                try: return x.decode('win1252', 'ignore').strip()
                except: return str(x)
            return str(x).strip() if x is not None else ''

        # Decodificações que dependem de blob/win1252 ainda usam map rápido
        df['EMPREENDIMENTO'] = df['EMPREENDIMENTO'].map(safe_decode)
        df['UNIDADE'] = df['UNIDADE'].map(safe_decode)
        df['COMPRADOR'] = df['COMPRADOR'].map(safe_decode)
        
        df['DATA_RECEBIMENTO'] = pd.to_datetime(df['DATA_RECEBIMENTO'], errors='coerce')
        df['RECEITA_CAIXA'] = df['RECEITA_CAIXA'].fillna(0.0).astype(float)
        df['VALORPARCELA'] = df['VALORPARCELA'].fillna(0.0).astype(float)
        df['VALORVARIACAO'] = df['VALORVARIACAO'].fillna(0.0).astype(float)
        df['VGV_BASE'] = df['VGV_BASE'].fillna(0.0).astype(float)
        
        df['RET_FLAG'] = df['RET'].astype(str).str.upper().str.strip() == 'S'
        df['DISTRATO_FLAG'] = df['DISTRATO'].astype(str).str.upper().str.strip() == 'S'
        
        df['VGV'] = np.where(df['DISTRATO_FLAG'], 0.0, df['VGV_BASE'])
        
        # Acréscimo
        acrescimo_base = np.maximum(0, df['RECEITA_CAIXA'] - df['VALORPARCELA'])
        df['ACRESCIMO'] = np.maximum(df['VALORVARIACAO'], acrescimo_base)
        
        # Módulo YM
        df['YM'] = df['DATA_RECEBIMENTO'].dt.to_period('M')
        # Filtro de Competência e Totalizadores Nativos
        # Para montar monthly_totals, filtramos ret == false
        df_non_ret_valid = df[(~df['RET_FLAG']) & (df['RECEITA_CAIXA'] > 0) & df['DATA_RECEBIMENTO'].notnull()]
        monthly_groups = df_non_ret_valid.groupby('YM')['RECEITA_CAIXA'].sum()
        
        # Computar month_adicional dicionário simulando a lógica iterativa nativa
        quarters_data = collections.defaultdict(list)
        for ym_period, m_total in monthly_groups.items():
            dt = ym_period.to_timestamp()
            ym = (dt.year, dt.month)
            yq = (dt.year, (dt.month - 1) // 3 + 1)
            quarters_data[yq].append(ym)
            
        monthly_totals_native = { (p.year, p.month): v for p, v in monthly_groups.items() }

        month_adicional = {}
        for yq, months in quarters_data.items():
            month3 = (yq[0], yq[1] * 3)
            month1 = (yq[0], yq[1] * 3 - 2)
            month2 = (yq[0], yq[1] * 3 - 1)
            
            quarter_base = monthly_totals_native.get(month1, 0) + monthly_totals_native.get(month2, 0) + monthly_totals_native.get(month3, 0)
            quarter_adicional = max(0, (quarter_base * 0.08) - 60000) * 0.10
            
            m1_adicional = max(0, (monthly_totals_native.get(month1, 0) * 0.08) - 20000) * 0.10
            m2_adicional = max(0, (monthly_totals_native.get(month2, 0) * 0.08) - 20000) * 0.10
            m3_adicional = quarter_adicional - m1_adicional - m2_adicional
            
            month_adicional[month1] = m1_adicional
            month_adicional[month2] = m2_adicional
            month_adicional[month3] = m3_adicional

        # Mapeando Tributos de volta pro df
        # Zerando colunas inicialmente
        for col in ['PIS', 'COFINS', 'IRPJ', 'CSLL', 'RET', 'IRPJ_ADICIONAL']:
            df[col] = 0.0
            
        # Para operações válidas (onde teve recebimento)
        mask_valid = (df['RECEITA_CAIXA'] > 0) & df['DATA_RECEBIMENTO'].notnull()
        m_ret = mask_valid & df['RET_FLAG']
        m_nret = mask_valid & (~df['RET_FLAG'])
        
        # RET Fix
        df.loc[m_ret, 'RET'] = df.loc[m_ret, 'RECEITA_CAIXA'] * 0.04
        
        # NRET Fix
        df.loc[m_nret, 'PIS'] = df.loc[m_nret, 'RECEITA_CAIXA'] * 0.0065
        df.loc[m_nret, 'COFINS'] = df.loc[m_nret, 'RECEITA_CAIXA'] * 0.03
        df.loc[m_nret, 'IRPJ'] = df.loc[m_nret, 'RECEITA_CAIXA'] * 0.012
        df.loc[m_nret, 'CSLL'] = df.loc[m_nret, 'RECEITA_CAIXA'] * 0.0108

        # IRPJ Adicional vetorizado via Series.map
        # Precisamos transformar YM nativo (Period) para tuple (Y, M) para bater com month_adicional keys
        # Para performance, fazemos o mapeamento no nível das chaves do período
        if len(month_adicional) > 0:
            def ym_to_tuple(period_val):
                if pd.isna(period_val): return (1900, 1)
                return (period_val.year, period_val.month)
            
            df_tuple_keys = df.loc[m_nret, 'YM'].map(ym_to_tuple)
            adicional_series = df_tuple_keys.map(lambda k: month_adicional.get(k, 0.0)).astype(float)
            total_m_series = df_tuple_keys.map(lambda k: monthly_totals_native.get(k, 0.0)).astype(float)
            
            fraction = df.loc[m_nret, 'RECEITA_CAIXA'] / total_m_series
            fraction = fraction.replace([np.inf, -np.inf, np.nan], 0)
            df.loc[m_nret, 'IRPJ_ADICIONAL'] = fraction * adicional_series

        df['TRIBUTOS_CAIXA_ACUMULADO'] = df['PIS'] + df['COFINS'] + df['IRPJ'] + df['CSLL'] + df['RET'] + df['IRPJ_ADICIONAL']
        
        # Window Masks para Mês (data_ini)
        target_ini_date = data_ini if data_ini else "1900-01-01"
        target_dt = pd.to_datetime(target_ini_date)
        is_mes_mask = df['DATA_RECEBIMENTO'] >= target_dt
        
        df['CAIXA_MES'] = np.where(is_mes_mask, df['RECEITA_CAIXA'], 0.0)
        df['ACRESCIMO_CAIXA_MES'] = np.where(is_mes_mask, df['ACRESCIMO'], 0.0)
        df['TRIBUTOS_CAIXA_MES'] = np.where(is_mes_mask, df['TRIBUTOS_CAIXA_ACUMULADO'], 0.0)
        for col in ['PIS', 'COFINS', 'IRPJ', 'CSLL', 'RET', 'IRPJ_ADICIONAL']:
            df[f'{col}_MES'] = np.where(is_mes_mask, df[col], 0.0)

        # Agrupamento no nível da Unidade Comercial
        unit_group = df.groupby(['EMPREENDIMENTO', 'UNIDADE', 'COMPRADOR', 'IDVENDA']).agg({
            'VGV': 'first',
            'RECEITA_CAIXA': 'sum',
            'CAIXA_MES': 'sum',
            'ACRESCIMO': 'sum',
            'ACRESCIMO_CAIXA_MES': 'sum',
            'TRIBUTOS_CAIXA_ACUMULADO': 'sum',
            'TRIBUTOS_CAIXA_MES': 'sum',
            'PIS': 'sum', 'PIS_MES': 'sum',
            'COFINS': 'sum', 'COFINS_MES': 'sum',
            'IRPJ': 'sum', 'IRPJ_MES': 'sum',
            'CSLL': 'sum', 'CSLL_MES': 'sum',
            'RET': 'sum', 'RET_MES': 'sum',
            'IRPJ_ADICIONAL': 'sum', 'IRPJ_ADICIONAL_MES': 'sum',
        }).reset_index()

        # Agora operamos POC (SQL -> Dict -> Map)
        emp_contas_by_name = {}
        poc_map = {}
        try:
            cur.execute("""
                SELECT ID, NOME, CONTACLI, CONTAADICLI, CONTAREC, CONTADESPESA, CONTACAIXA, 
                       CONTAVARIACAO, CONTAESTAND, CONTAESTCON, CONTACUSTO, 
                       CONTADEVOLUCAO, CONTALUCROACUM, CONTA_ESTORNO_DEVOLUCAO, OBRACONCLUIDA
                FROM EMPREENDIMENTO
            """)
            emps_all = cur.fetchall()
            for ev in emps_all:
                emp_name_str = (ev[1].decode('win1252', 'ignore').strip() if isinstance(ev[1], bytes) else str(ev[1]).strip()) if ev[1] else str(ev[0])
                emp_contas_by_name[emp_name_str] = {
                    "CONTACLI": ev[2] if len(ev) > 2 and ev[2] else "CLIENTES",
                    "CONTAADICLI": ev[3] if len(ev) > 3 and ev[3] else "ADIAN DE CLIENTES",
                    "CONTAREC": ev[4] if len(ev) > 4 and ev[4] else "RECEITA DE VENDAS DRE",
                    "CONTADESPESA": ev[5] if len(ev) > 5 and ev[5] else "DESPESA TRIBUTARIA DRE",
                    "CONTACAIXA": ev[6] if len(ev) > 6 and ev[6] else "BANCOS CONTA MOVIMENTO",
                    "CONTAVARIACAO": ev[7] if len(ev) > 7 and ev[7] else "RECEITA DE VARIACOES DRE",
                    "CONTAESTAND": ev[8] if len(ev) > 8 and ev[8] else "ESTOQUE EM ANDAMENTO",
                    "CONTAESTCON": ev[9] if len(ev) > 9 and ev[9] else "ESTOQUE CONCLUIDO",
                    "CONTACUSTO": ev[10] if len(ev) > 10 and ev[10] else "CMV",
                    "CONTADEVOLUCAO": ev[11] if len(ev) > 11 and ev[11] else "DISTRATOS DRE",
                    "CONTALUCROACUM": ev[12] if len(ev) > 12 and ev[12] else "LUCROS ACUMULADOS",
                    "CONTA_ESTORNO_DEVOLUCAO": ev[13] if len(ev) > 13 and ev[13] else "ESTORNOS DISTRATOS DRE"
                }
                is_concluida = str(ev[14]).strip().upper() == 'S' if len(ev) > 14 and ev[14] else False
                if is_concluida:
                    poc_map[(emp_name_str, '2000-01')] = 100.0
        except Exception as e:
            print("POC/Empresa Warning:", e)
            
        try:
            cur.execute("""
                SELECT e.NOME, p.PERIODO, p.PERCENTUAL 
                FROM POC p JOIN EMPREENDIMENTO e ON p.ID_EMPREENDIMENTO = e.ID
            """)
            for row in cur.fetchall():
                emp_nome, periodo, p = row
                if not emp_nome or not periodo: continue
                emp_name_str = (emp_nome.decode('win1252', 'ignore').strip() if isinstance(emp_nome, bytes) else str(emp_nome).strip())
                p_str = (periodo.decode('win1252', 'ignore').strip() if isinstance(periodo, bytes) else str(periodo).strip())
                ym_key = p_str[:7]
                current_val = poc_map.get((emp_name_str, ym_key), 0.0)
                raw_p = float(p or 0)
                capped_p = raw_p if raw_p <= 100.0 else 100.0
                poc_map[(emp_name_str, ym_key)] = max(current_val, capped_p)
        except Exception as e:
            print("Aviso Lendo POC Oficial Vulcano:", e)
            
        poc_list_by_emp = collections.defaultdict(list)
        for (p_emp, val_ym), p_val in poc_map.items():
            poc_list_by_emp[p_emp].append((val_ym, p_val / 100.0))
        for k in poc_list_by_emp:
            poc_list_by_emp[k].sort(key=lambda x: x[0])

        anchor_ym = data_fim[:7] if data_fim else datetime.datetime.now().strftime("%Y-%m")
        
        def get_poc_at_or_before(emp_name, target_ym_str):
            best_poc = 0.0
            for ym_key, val in poc_list_by_emp.get(emp_name, []):
                if ym_key <= target_ym_str: best_poc = val
                else: break
            return best_poc

        def get_poc_strictly_before(emp_name, target_ym_str):
            best_poc = 0.0
            for ym_key, val in poc_list_by_emp.get(emp_name, []):
                if ym_key < target_ym_str: best_poc = val
                else: break
            return best_poc

        # Consolidação Emp (Nível 1)
        # Ao invés de usar pandas para isso, construímos o dictionary nativo `dashboard_meta` e o json flat `data`
        # Isso é super rápido agora que iteramos sobre as unidades agrupadas (centenas, não mais centenas de milhares)
        
        dashboard_meta = collections.defaultdict(lambda: {
             "vgv": 0.0, "poc": 0.0, "poc_anterior": 0.0, "poc_mes": 0.0,
             "receita_societaria": 0.0, "receita_soc_mes": 0.0,
             "caixa_acumulado": 0.0, "caixa_mes": 0.0,
             "tributos_caixa_acumulado": 0.0, "tributos_caixa_mes": 0.0,
             "tributos_soc_acumulado": 0.0, "tributos_soc_mes": 0.0,
             "unidades": []
        })

        data_export = []
        for row in unit_group.itertuples(index=False):
            emp = str(row.EMPREENDIMENTO)
            uni = str(row.UNIDADE)
            comp = str(row.COMPRADOR)
            
            # Setup initial POC if new EMP
            if dashboard_meta[emp]["poc_mes"] == 0 and dashboard_meta[emp]["poc"] == 0:
                poc_acumulado = get_poc_at_or_before(emp, anchor_ym)
                poc_anterior = get_poc_strictly_before(emp, anchor_ym)
                poc_mes = max(0, poc_acumulado - poc_anterior)
                dashboard_meta[emp]["poc"] = poc_acumulado * 100.0
                dashboard_meta[emp]["poc_anterior"] = poc_anterior * 100.0
                dashboard_meta[emp]["poc_mes"] = poc_mes * 100.0
                dashboard_meta[emp]["contas_contabeis"] = emp_contas_by_name.get(emp, {})
                
            poc_acumulado = dashboard_meta[emp]["poc"] / 100.0
            poc_mes = dashboard_meta[emp]["poc_mes"] / 100.0
            
            soc_acumulada_uni = row.VGV * poc_acumulado
            soc_mes_uni = row.VGV * poc_mes
            
            eff_rate_acum = (row.TRIBUTOS_CAIXA_ACUMULADO / row.RECEITA_CAIXA) if row.RECEITA_CAIXA > 0 else 0
            eff_rate_mes = (row.TRIBUTOS_CAIXA_MES / row.CAIXA_MES) if row.CAIXA_MES > 0 else 0
            
            tributos_soc_acumulada_uni = soc_acumulada_uni * eff_rate_acum
            tributos_soc_mes_uni = soc_mes_uni * eff_rate_mes
            
            # Aggregating into Dashboard Meta Empreendimento
            meta_emp = dashboard_meta[emp]
            meta_emp["vgv"] += row.VGV
            meta_emp["receita_societaria"] += soc_acumulada_uni
            meta_emp["receita_soc_mes"] += soc_mes_uni
            meta_emp["caixa_acumulado"] += row.RECEITA_CAIXA
            meta_emp["caixa_mes"] += row.CAIXA_MES
            meta_emp["tributos_caixa_acumulado"] += row.TRIBUTOS_CAIXA_ACUMULADO
            meta_emp["tributos_caixa_mes"] += row.TRIBUTOS_CAIXA_MES
            meta_emp["tributos_soc_acumulado"] += tributos_soc_acumulada_uni
            meta_emp["tributos_soc_mes"] += tributos_soc_mes_uni
            
            meta_emp["unidades"].append({
                "unidade": uni, "comprador": comp, "vgv": row.VGV,
                "caixa_acumulado": row.RECEITA_CAIXA, "caixa_mes": row.CAIXA_MES,
                "soc_acumulado": soc_acumulada_uni, "soc_mes": soc_mes_uni,
                "tributos_caixa_acumulado": row.TRIBUTOS_CAIXA_ACUMULADO, "tributos_caixa_mes": row.TRIBUTOS_CAIXA_MES,
                "tributos_soc_acumulado": tributos_soc_acumulada_uni, "tributos_soc_mes": tributos_soc_mes_uni,
                "trib_detalhe_caixa_acumulado": {
                    "pis": row.PIS, "cofins": row.COFINS, "irpj": row.IRPJ, 
                    "csll": row.CSLL, "ret": row.RET, "irpj_adicional": row.IRPJ_ADICIONAL
                },
                "trib_detalhe_caixa_mes": {
                    "pis": row.PIS_MES, "cofins": row.COFINS_MES, "irpj": row.IRPJ_MES, 
                    "csll": row.CSLL_MES, "ret": row.RET_MES, "irpj_adicional": row.IRPJ_ADICIONAL_MES
                }
            })
            
            # Flat Data for UI rendering
            data_export.append({
                "estabelecimento": "1", "empreendimento": emp, "unidade": uni, "comprador": comp,
                "periodo": anchor_ym + "-01", "vgv": row.VGV,
                "receita_caixa": row.CAIXA_MES, "base_calculo": row.CAIXA_MES,
                "receita_societaria": soc_mes_uni, "poc": meta_emp["poc"],
                "pis": row.PIS_MES, "cofins": row.COFINS_MES, "irpj": row.IRPJ_MES, "csll": row.CSLL_MES, "ret": row.RET_MES,
                "tributos_total": row.TRIBUTOS_CAIXA_MES, "tributos_societario": tributos_soc_mes_uni,
                "saldo_clientes": max(0, soc_acumulada_uni - row.RECEITA_CAIXA),
                "saldo_tributos": max(0, row.RECEITA_CAIXA - soc_acumulada_uni),
                "caixa_acumulado": row.RECEITA_CAIXA, "soc_acumulado": soc_acumulada_uni,
                "tributos_caixa_acumulado": row.TRIBUTOS_CAIXA_ACUMULADO, "tributos_soc_acumulado": tributos_soc_acumulada_uni
            })

        conn.close()
        return {"dashboard_data": data_export, "ret_consolidado": [], "dashboard_meta": dashboard_meta}
    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
'''

with codecs.open('backend/main.py', 'r', 'utf-8') as f:
    content = f.read()

import re
# Regex to replace the function completely
# Escaping the complexity by matching up up to get_compare_pessoas
pattern = re.compile(r'@app\.get\("/api/receitas-caixa"\).*?(?=@app\.get\("/api/compare/pessoas"\))', re.DOTALL)
if pattern.search(content):
    content = pattern.sub(new_func + "\n", content)
    with codecs.open('backend/main.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Replaced!")
else:
    print("Pattern not found!")
