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
            join_conditions += " AND r.DATA <= ?"
            params.insert(0, data_fim)
        
        if data_ini:
            join_conditions += " AND r.DATA >= ?"
            params.append(data_ini)
            
        query = query.replace("AND r.TOTALPAGO > 0", "AND r.TOTALPAGO > 0" + join_conditions)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Performance: read_sql_query with chunksize or just raw fetch for Firebird often varies
        # But we'll keep it as is, ensuring the JOIN conditions limit the set early.
        query += " ORDER BY r.DATA DESC NULLS LAST"
        
        df = pd.read_sql_query(query, conn, params=tuple(params))
        # Global Sanitization
        df = df.replace({np.nan: 0.0}) 
        
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
