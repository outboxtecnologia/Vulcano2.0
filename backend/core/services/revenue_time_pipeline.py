import pandas as pd
import numpy as np
import collections
import datetime
from fastapi import HTTPException

class RevenueTimePipeline:
    @staticmethod
    def get_receitas_caixa(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, empreendimentos_ids: str | None = None):
        from main import get_conn

        # Pandas Vectorized Engine Start
        import pandas as pd
        import numpy as np
        import collections
        import datetime
        import calendar
        
        if data_ini and len(data_ini) == 7:
            data_ini = f"{data_ini}-01"
        if data_fim and len(data_fim) == 7:
            # Pega o ultimo dia do mes
            y, m = map(int, data_fim.split("-"))
            last_day = calendar.monthrange(y, m)[1]
            data_fim = f"{data_fim}-{last_day:02d}"
        
        conn = get_conn("vulcano")
        cur = conn.cursor()
    
        query = """
        SELECT 
            v.CODIGOEMPRESA,
            v.CODIGOESTAB,
            e.NOME AS EMPREENDIMENTO,
            v.DESCUNIDIMOB AS UNIDADE,
            c.NOME AS COMPRADOR,
            r.DATA AS DATA_RECEBIMENTO,
            CASE 
                WHEN UPPER(fp.DESCRICAO) LIKE '%PERMUTA%' AND r.TOTALPAGO = 0 THEN r.VALORPARCELA 
                ELSE r.TOTALPAGO 
            END AS RECEITA_CAIXA,
            r.VALORPARCELA,
            r.VALORVARIACAO,
            v.TOTALVENDA AS VGV_BASE,
            e.RET,
            v.DISTRATO,
            v.DATADISTRATO,
            v.ID AS IDVENDA,
            v.DTOPER AS DATA_VENDA,
            e.CODIGOHISTRECEBIMENTO,
            e.CODIGOHISTVARIACAO,
            e.CODIGOHISTVENDA
        FROM VENDA v
        JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
        LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
        LEFT JOIN RECEBER r ON r.IDVENDA = v.ID 
        LEFT JOIN VENDAFORMAPAGTO fp ON r.IDVENDAFORMAPAGTO = fp.ID
        WHERE (r.TOTALPAGO > 0 OR UPPER(fp.DESCRICAO) LIKE '%PERMUTA%')
        """
        
        try:
            conditions = []
            params = []
            if empresa_id is not None:
                conditions.append("v.CODIGOEMPRESA = ?")
                params.append(int(empresa_id))
                
            if empreendimentos_ids:
                # Parse comma-separated string to list of ints
                try:
                    emp_list = [int(p.strip()) for p in empreendimentos_ids.split(",") if p.strip()]
                    if emp_list:
                        # Create IN clause with placeholders
                        placeholders = ",".join(["?"] * len(emp_list))
                        conditions.append(f"e.ID IN ({placeholders})")
                        params.extend(emp_list)
                except ValueError:
                    pass
    
            
            join_conditions = ""
            join_params = []
            
            if data_fim:
                join_conditions += " AND r.DATA <= ?"
                join_params.append(data_fim)
                
            if data_ini:
                join_conditions += " AND r.DATA >= ?"
                join_params.append(data_ini)
            
            query = query.replace("WHERE (r.TOTALPAGO > 0 OR UPPER(fp.DESCRICAO) LIKE '%PERMUTA%')", "WHERE (r.TOTALPAGO > 0 OR UPPER(fp.DESCRICAO) LIKE '%PERMUTA%')" + join_conditions)
                
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            query += " ORDER BY r.DATA DESC NULLS LAST"
            
            df = pd.read_sql_query(query, conn, params=tuple(join_params + params))
            # Salvar as colunas numéricas que não queremos que virem 0.0 se forem NaN (como os códigos de histórico que podem ser None)
            _dv_backup = df['DATA_VENDA'].copy()
            _hist_rec = df['CODIGOHISTRECEBIMENTO'].copy()
            _hist_var = df['CODIGOHISTVARIACAO'].copy()
            _hist_venda = df['CODIGOHISTVENDA'].copy()
    
            # Global Sanitization
            df = df.replace({np.nan: 0.0})
            
            df['CODIGOHISTRECEBIMENTO'] = _hist_rec.fillna(0).astype(int)
            df['CODIGOHISTVARIACAO'] = _hist_var.fillna(0).astype(int)
            df['CODIGOHISTVENDA'] = _hist_venda.fillna(0).astype(int)
    
            # Restaurar DATA_VENDA: converte para string 'YYYY-MM-DD' ou None de forma robusta
            _invalidos = {'', '0', '0.0', 'nan', 'NaT', 'None', 'nat', 'none'}
            def _safe_date(v):
                if v is None: return None
                s = str(v)
                if s in _invalidos: return None
                try:
                    return str(pd.Timestamp(v))[:10]  # 'YYYY-MM-DD'
                except Exception:
                    return None
            df['DATA_VENDA'] = _dv_backup.apply(_safe_date)
    
            
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
            
            # Vectorized Module YM (Period)
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
    
            # Fetch Locações History from Questor to compute PROPORTIONAL Adicional Mixed Base
            monthly_locacoes = {}
            try:
                conn_q = get_conn("questor")
                cur_q = conn_q.cursor()
                cur_q.execute("""
                    SELECT EXTRACT(YEAR FROM I.DATALCTOFIS), EXTRACT(MONTH FROM I.DATALCTOFIS), SUM(C.VALORCONTABILIMPOSTO)
                    FROM LCTOFISSAICFOP C
                    JOIN LCTOFISSAI I ON C.CODIGOEMPRESA = I.CODIGOEMPRESA AND C.CODIGOESTAB = I.CODIGOESTAB AND C.CHAVELCTOFISSAI = I.CHAVELCTOFISSAI
                    WHERE C.CODIGOEMPRESA = ? AND C.CODIGOCFOP IN (9000200, 9000201)
                    GROUP BY 1, 2
                """, (int(empresa_id) if empresa_id else 0,))
                monthly_locacoes = {(int(r[0]), int(r[1])): float(r[2] or 0.0) for r in cur_q.fetchall()}
                conn_q.close()
            except Exception as e:
                print("Erro ao buscar historico de locacoes:", e)
    
            month_adicional = {}
            for yq, months in quarters_data.items():
                month3 = (yq[0], yq[1] * 3)
                month1 = (yq[0], yq[1] * 3 - 2)
                month2 = (yq[0], yq[1] * 3 - 1)
                
                qb_vendas = monthly_totals_native.get(month1, 0) + monthly_totals_native.get(month2, 0) + monthly_totals_native.get(month3, 0)
                qb_locacoes = monthly_locacoes.get(month1, 0) + monthly_locacoes.get(month2, 0) + monthly_locacoes.get(month3, 0)
                
                # Cálculo de Adicional Misto (Vendas a 8% + Locações a 32%) - Rateado pelo Peso do Eixo
                lucro_presumido_misto = (qb_vendas * 0.08) + (qb_locacoes * 0.32)
                quarter_adicional_global = max(0.0, lucro_presumido_misto - 60000.0) * 0.10
                
                fracao_vendas = (qb_vendas * 0.08) / lucro_presumido_misto if lucro_presumido_misto > 0 else 0
                adicional_vendas_trimestre = quarter_adicional_global * fracao_vendas
                
                # Distribui do trimestre proporcional à base de cada mês nativo (para não distorcer UI)
                m1_vendas = monthly_totals_native.get(month1, 0) * 0.08
                m2_vendas = monthly_totals_native.get(month2, 0) * 0.08
                
                m1_adicional = adicional_vendas_trimestre * (m1_vendas / (qb_vendas * 0.08)) if qb_vendas > 0 else 0
                m2_adicional = adicional_vendas_trimestre * (m2_vendas / (qb_vendas * 0.08)) if qb_vendas > 0 else 0
                m3_adicional = adicional_vendas_trimestre - m1_adicional - m2_adicional
                
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
    
            # Se houver data_ini, faremos uma micro-query de todo o histórico puramente numérico (Super rápida)
            # Para resgatar o Saldo Acumulado sem estourar 2 minutos travando no JOIN de nomes e strings velhos
            if data_ini:
                cur.execute(f"""
                    SELECT r.IDVENDA, 
                           SUM(CASE WHEN UPPER(fp.DESCRICAO) LIKE '%PERMUTA%' AND r.TOTALPAGO = 0 THEN r.VALORPARCELA ELSE r.TOTALPAGO END), 
                           SUM(r.VALORVARIACAO)
                    FROM RECEBER r
                    JOIN VENDA v ON r.IDVENDA = v.ID
                    LEFT JOIN VENDAFORMAPAGTO fp ON r.IDVENDAFORMAPAGTO = fp.ID
                    WHERE r.DATA < ? 
                      AND (r.TOTALPAGO > 0 OR UPPER(fp.DESCRICAO) LIKE '%PERMUTA%') 
                      AND v.CODIGOEMPRESA = ?
                    GROUP BY r.IDVENDA
                """, [data_ini, int(empresa_id) if empresa_id else 0])
                hist_rows = cur.fetchall()
                if hist_rows:
                    # Processamento relâmpago do Acumulado Histórico para Vendas Existentes
                    hist_dict = {row[0]: (row[1] or 0.0, row[2] or 0.0) for row in hist_rows}
                    
                    # Mapeando os recibos passados de volta para nosso df principal agregado de forma vetorial
                    def sum_hist_caixa(vid): return float(hist_dict.get(vid, (0.0, 0.0))[0])
                    def sum_hist_acres(vid): return float(hist_dict.get(vid, (0.0, 0.0))[1])
                    
                    df['HIST_CAIXA'] = df['IDVENDA'].apply(sum_hist_caixa)
                    df['HIST_ACRES'] = df['IDVENDA'].apply(sum_hist_acres)
                    
                    # A RECEITA_CAIXA global passa a contemplar as parcelas pagas no passado
                    df['RECEITA_CAIXA'] = df['RECEITA_CAIXA'] + df['HIST_CAIXA']
                    df['ACRESCIMO'] = df['ACRESCIMO'] + df['HIST_ACRES']
                    
                    # Recalcula Taxa Acumulada da Base Histórica simplificada
                    # Aplicamos a % efetiva do mês transacionado (RET/PRES) sobre a massa passada
                    rate_mes = df['TRIBUTOS_CAIXA_MES'] / df['CAIXA_MES']
                    rate_mes = rate_mes.fillna(0.0).replace([np.inf, -np.inf], 0.0)
                    
                    # Se CAIXA_MES for 0 (Sem pagamentos novos), a taxa assumida será RET (4%) ou PIS/COFINS (5.93%)
                    fallback_rate = np.where(df['RET_FLAG'], 0.04, 0.0593)
                    final_rate = np.where(df['CAIXA_MES'] > 0, rate_mes, fallback_rate)
                    
                    df['TRIBUTOS_CAIXA_ACUMULADO'] = df['TRIBUTOS_CAIXA_ACUMULADO'] + (df['HIST_CAIXA'] * final_rate)
                    
            # Agrupamento no nível da Unidade Comercial
            unit_group = df.groupby(['EMPREENDIMENTO', 'UNIDADE', 'COMPRADOR', 'IDVENDA']).agg({
                'VGV': 'first',
                'DATA_VENDA': 'first',
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
                    SELECT REPLACE(C.CLASSIFICACAO, '.', ''), CX.DESCRICAO 
                    FROM CONTA_CONTABIL C 
                    JOIN CONTA CX ON C.ID_CONTA = CX.NOCONTA
                """)
                nomes_contas = {str(r[0]).strip(): (r[1].decode('win1252', 'ignore') if isinstance(r[1], bytes) else str(r[1])).strip() for r in cur.fetchall()}
                
                def fmt_cta(codigo, default_desc):
                    if not codigo: return default_desc
                    c = str(codigo).strip()
                    desc = nomes_contas.get(c, default_desc)
                    return f"{c} - {desc}"
    
                query_emp = """
                    SELECT ID, NOME, CONTACLI, CONTAADICLI, CONTAREC, CONTADESPESA, CONTACAIXA, 
                           CONTAVARIACAO, CONTAESTAND, CONTAESTCON, CONTACUSTO, 
                           CONTADEVOLUCAO, CONTALUCROACUM, CONTA_ESTORNO_DEVOLUCAO, OBRACONCLUIDA
                    FROM EMPREENDIMENTO
                """
                if empresa_id is not None:
                    query_emp += " WHERE CODIGOEMPRESA = ?"
                    cur.execute(query_emp, (empresa_id,))
                else:
                    cur.execute(query_emp)
                emps_all = cur.fetchall()
                for ev in emps_all:
                    emp_name_str = (ev[1].decode('win1252', 'ignore').strip() if isinstance(ev[1], bytes) else str(ev[1]).strip()) if ev[1] else str(ev[0])
                    
                    emp_contas_by_name[emp_name_str] = {
                        "CONTACLI": fmt_cta(ev[2] if len(ev) > 2 else None, "CLIENTES"),
                        "CONTAADICLI": fmt_cta(ev[3] if len(ev) > 3 else None, "ADIAN DE CLIENTES"),
                        "CONTAREC": fmt_cta(ev[4] if len(ev) > 4 else None, "RECEITA DE VENDAS DRE"),
                        "CONTADESPESA": fmt_cta(ev[5] if len(ev) > 5 else None, "DESPESA TRIBUTARIA DRE"),
                        "CONTACAIXA": fmt_cta(ev[6] if len(ev) > 6 else None, "BANCOS CONTA MOVIMENTO"),
                        "CONTAVARIACAO": fmt_cta(ev[7] if len(ev) > 7 else None, "RECEITA DE VARIACOES DRE"),
                        "CONTAESTAND": fmt_cta(ev[8] if len(ev) > 8 else None, "ESTOQUE EM ANDAMENTO"),
                        "CONTAESTCON": fmt_cta(ev[9] if len(ev) > 9 else None, "ESTOQUE CONCLUIDO"),
                        "CONTACUSTO": fmt_cta(ev[10] if len(ev) > 10 else None, "CMV"),
                        "CONTADEVOLUCAO": fmt_cta(ev[11] if len(ev) > 11 else None, "DISTRATOS DRE"),
                        "CONTALUCROACUM": fmt_cta(ev[12] if len(ev) > 12 else None, "LUCROS ACUMULADOS"),
                        "CONTA_ESTORNO_DEVOLUCAO": fmt_cta(ev[13] if len(ev) > 13 else None, "ESTORNOS DISTRATOS DRE")
                    }
                    is_concluida = str(ev[14]).strip().upper() == 'S' if len(ev) > 14 and ev[14] else False
                    if is_concluida:
                        poc_map[(emp_name_str, '2000-01')] = 100.0
            except Exception as e:
                print("POC/Empresa Warning:", e)
                
            try:
                query_poc = """
                    SELECT e.NOME, p.PERIODO, p.PERCENTUAL 
                    FROM POC p JOIN EMPREENDIMENTO e ON p.ID_EMPREENDIMENTO = e.ID
                """
                if empresa_id is not None:
                    query_poc += " WHERE e.CODIGOEMPRESA = ?"
                    cur.execute(query_poc, (empresa_id,))
                else:
                    cur.execute(query_poc)
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
                 "pis": 0.0, "cofins": 0.0, "csll": 0.0, "irpj": 0.0, "ret": 0.0, "irpj_adicional": 0.0,
                 "unidades": []
            })
    
            data_export = []
            for row in unit_group.itertuples(index=False):
                emp = str(row.EMPREENDIMENTO)
                uni = str(row.UNIDADE)
                comp = str(row.COMPRADOR)
                
                # Setup initial POC if new EMP
                if dashboard_meta[emp]["poc_mes"] == 0 and dashboard_meta[emp]["poc"] == 0:
                    final_ym = data_fim[:7] if data_fim else datetime.datetime.now().strftime("%Y-%m")
                    start_ym = data_ini[:7] if data_ini else None
                    
                    poc_ac_temp = get_poc_at_or_before(emp, final_ym)
                    poc_ant_temp = get_poc_strictly_before(emp, start_ym) if start_ym else 0.0
                    poc_mes = max(0, poc_ac_temp - poc_ant_temp)
                    
                    dashboard_meta[emp]["poc"] = poc_ac_temp * 100.0
                    dashboard_meta[emp]["poc_anterior"] = poc_ant_temp * 100.0
                    dashboard_meta[emp]["poc_mes"] = poc_mes * 100.0
                    dashboard_meta[emp]["contas_contabeis"] = emp_contas_by_name.get(emp, {})
                    dashboard_meta[emp]["historico_poc"] = [{"periodo": x[0], "poc": x[1]*100} for x in poc_list_by_emp.get(emp, [])]
                    
                poc_acumulado = dashboard_meta[emp]["poc"] / 100.0
                poc_mes = dashboard_meta[emp]["poc_mes"] / 100.0
                
                soc_acumulada_uni = row.VGV * poc_acumulado
                soc_mes_uni = row.VGV * poc_mes
                
                eff_rate_acum = (row.TRIBUTOS_CAIXA_ACUMULADO / row.RECEITA_CAIXA) if row.RECEITA_CAIXA > 0 else 0
                
                tributos_soc_acumulada_uni = soc_acumulada_uni * eff_rate_acum
                # Usar a taxa efetiva acumulada do histórico da unidade para prever passivo tributário sobre o crescimento do POC no período
                tributos_soc_mes_uni = soc_mes_uni * eff_rate_acum
                
                # Filtro Poda de UI (Zerar visual da UI para unidades ociosas que não tenham pendência fiscal considerável)
                is_idle = (row.CAIXA_MES == 0) and (soc_mes_uni == 0)
                pending_diff = abs(tributos_soc_acumulada_uni - row.TRIBUTOS_CAIXA_ACUMULADO)
    
                # NUNCA pular unidades cuja venda ocorreu no mês alvo:
                # mesmo sem recebimento ainda (boleto cai no mês seguinte), o motor
                # de contabilizacoes precisa enxergá-la para gerar D Clientes / C Receita.
                data_venda_row = str(row.DATA_VENDA)[:7] if row.DATA_VENDA and str(row.DATA_VENDA) not in ('0', '', 'None', 'nan', '0.0') else ''
                target_ym_rcx = data_ini[:7] if data_ini else ''
                is_nova_venda_no_mes = bool(data_venda_row) and bool(target_ym_rcx) and (data_venda_row == target_ym_rcx)
    
                # DEBUG temporário
                # (removido)
    
                if is_idle and pending_diff < 5.0 and data_ini is not None and not is_nova_venda_no_mes:
                    continue # Pula unidade completamente
    
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
                
                meta_emp["pis"] += row.PIS
                meta_emp["cofins"] += row.COFINS
                meta_emp["csll"] += row.CSLL
                meta_emp["irpj"] += row.IRPJ
                meta_emp["ret"] += row.RET
                meta_emp["irpj_adicional"] += row.IRPJ_ADICIONAL
                
    
                meta_emp["unidades"].append({
                    "unidade": uni, "comprador": comp, "vgv": row.VGV,
                    "data_venda": str(row.DATA_VENDA)[:10] if row.DATA_VENDA and str(row.DATA_VENDA) not in ('0', '', 'None', 'nan', '0.0') else None,
                    "caixa_acumulado": row.RECEITA_CAIXA, "caixa_mes": row.CAIXA_MES,
                    # Acréscimos (Variação Monetária) separados do principal
                    # acrescimo_acumulado = soma de todos acréscimos recebidos até data_fim
                    # acrescimo_mes      = acréscimos recebidos apenas no mês-alvo
                    "acrescimo_acumulado": row.ACRESCIMO,
                    "acrescimo_mes": row.ACRESCIMO_CAIXA_MES,
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
    
            # Native Evolution Timeline using only current period receipts 
            # (Ignore massive legacy accumulation dumps on timeline bounds)
            timeline_grouped = df[df['CAIXA_MES'] > 0].groupby('YM').agg({
                 'CAIXA_MES': 'sum',
                 'TRIBUTOS_CAIXA_MES': 'sum'
            }).reset_index()
            
            dashboard_timeline = []
            for row in timeline_grouped.itertuples(index=False):
                 dashboard_timeline.append({
                      "periodo": str(row.YM),
                      "caixa": row.CAIXA_MES,
                      "trib": row.TRIBUTOS_CAIXA_MES
                 })
    
            valid_dashboard_meta = {k: v for k, v in dashboard_meta.items() if len(v["unidades"]) > 0}
    
            cur.execute("SELECT * FROM IMPOSTO")
            imposto_cols = [desc[0].strip() for desc in cur.description]
            imposto_rows = cur.fetchall()
            impostos_config = []
            import decimal
            for r in imposto_rows:
                d = {}
                for i, c in enumerate(imposto_cols):
                    val = r[i]
                    if isinstance(val, decimal.Decimal): val = float(val)
                    if isinstance(val, bytes): val = val.decode('cp1252', 'ignore')
                    elif isinstance(val, str): val = val.strip()
                    d[c] = val
                impostos_config.append(d)
    
            conn.close()
            return {
                "impostos_config": impostos_config,
                "dashboard_data": data_export, 
                "ret_consolidado": [], 
                "dashboard_meta": valid_dashboard_meta,
                "dashboard_timeline": dashboard_timeline
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            if 'conn' in locals() and conn: conn.close()
            raise HTTPException(status_code=500, detail=str(e))
    