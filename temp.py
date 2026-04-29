import sys
import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('@app.get("/api/vulcano/recebimentos")')
end_idx = content.find('class BaixaInput(BaseModel):', start_idx)

new_func = """@app.get("/api/vulcano/recebimentos")
def get_vulcano_recebimentos(empresa_id: int, empreendimento_id: int = None, data_ini: str = None, data_fim: str = None):
    import sqlite3
    import pandas as pd
    import numpy as np
    s_conn = None
    conn = None
    try:
        locais = {}
        try:
            s_conn = sqlite3.connect(POC_DATABASE_FILE)
            s_curr = s_conn.cursor()
            s_curr.execute("SELECT id_receber, valor_pago, data_pagamento, descontos, acrescimos FROM operacoes_baixas WHERE empresa_id = ?", (empresa_id,))
            locais = {row[0]: row for row in s_curr.fetchall()}
        except Exception as e:
            pass
        finally:
            if s_conn: s_conn.close()
            
        conn = get_conn("vulcano")
        query = '''
            SELECT r.DATA, r.TOTALPAGO, r.VALORPARCELA, r.VALORVARIACAO, v.DESCUNIDIMOB, c.CNPJ, r.PARCELA, c.NOME AS CLIENTE_NOME, e.NOME AS EMPREENDIMENTO, r.OBS, r.ID, v.TOTALVENDA, r.DESCONTO, v.ID AS VENDA_ID
            FROM VENDA v
            JOIN RECEBER r ON r.IDVENDA = v.ID
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE v.CODIGOEMPRESA = ?
        '''
        params = [empresa_id]
        
        if empreendimento_id:
            query += " AND v.IDEMPREENDIMENTO = ?"
            params.append(empreendimento_id)
            
        if data_ini:
            query += " AND r.DATA >= CAST(? AS DATE)"
            params.append(data_ini)
            
        if data_fim:
            query += " AND r.DATA <= CAST(? AS DATE)"
            params.append(data_fim)
            
        query += " ORDER BY r.DATA ASC"
        
        df = pd.read_sql_query(query, conn, params=tuple(params))
        df = df.replace({np.nan: None})

        def safe_dec(x):
            if isinstance(x, bytes):
                return x.decode('cp1252', 'ignore').strip()
            return str(x).strip() if x is not None else ""

        for col in ['DESCUNIDIMOB', 'CNPJ', 'PARCELA', 'CLIENTE_NOME', 'EMPREENDIMENTO', 'OBS']:
            if col in df.columns:
                df[col] = df[col].map(safe_dec)

        df['DATA_STR'] = pd.to_datetime(df['DATA'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
        df['DATA_ISO'] = pd.to_datetime(df['DATA'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        df['TOTALPAGO'] = df['TOTALPAGO'].fillna(0).astype(float)
        df['VALORPARCELA'] = df['VALORPARCELA'].fillna(0).astype(float)
        df['VALORVARIACAO'] = df['VALORVARIACAO'].fillna(0).astype(float)
        df['DESCONTO'] = df['DESCONTO'].fillna(0).astype(float)

        df_mapped = df.rename(columns={
            'ID': 'id',
            'DATA_STR': 'data',
            'DATA_ISO': 'vencimento_iso',
            'TOTALPAGO': 'total',
            'VALORPARCELA': 'parcela',
            'VALORVARIACAO': 'variacao',
            'DESCUNIDIMOB': 'descricao_venda',
            'CNPJ': 'cliente_cnpj',
            'PARCELA': 'num_parcela',
            'CLIENTE_NOME': 'cliente',
            'EMPREENDIMENTO': 'empreendimento',
            'OBS': 'obs',
            'DESCONTO': 'desconto',
            'VENDA_ID': 'venda_id'
        }).fillna('')
        
        result_list = df_mapped[['id', 'data', 'vencimento_iso', 'total', 'parcela', 'variacao', 'descricao_venda', 'cliente_cnpj', 'num_parcela', 'cliente', 'empreendimento', 'obs', 'desconto', 'venda_id']].to_dict('records')
        
        assinaturas_receber = set()
        
        for item in result_list:
            rid = item['id']
            
            v_id = item.get('venda_id')
            d_iso = item.get('vencimento_iso')
            val = float(item.get('parcela') or 0)
            if v_id and d_iso:
                assinaturas_receber.add((v_id, d_iso, round(val, 2)))
                
            if rid in locais:
                db_l = locais[rid]
                item['total'] = db_l[1]
                item['data_pagamento'] = db_l[2]
                item['desconto_local'] = db_l[3]
                item['acrescimo_local'] = db_l[4]
                item['status_sistema'] = 'BAIXADO_NOVO'
            else:
                item['data_pagamento'] = ''
                item['desconto_local'] = 0.0
                item['acrescimo_local'] = 0.0
                item['status_sistema'] = 'BAIXADO_LEGADO' if float(item.get('total', 0) or 0) > 0 else 'ABERTO'
                
        # --- PARCELAS ABERTAS PROJETADAS ---
        try:
            conn_sq = get_conn("sqlite")
            cur_sq = conn_sq.cursor()
            
            query_v = '''
                SELECT v.ID, v.DESCUNIDIMOB, c.CNPJ, c.NOME AS CLIENTE_NOME, e.NOME AS EMPREENDIMENTO
                FROM VENDA v
                LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
                LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
                WHERE v.CODIGOEMPRESA = ?
            '''
            params_v = [empresa_id]
            if empreendimento_id:
                query_v += " AND v.IDEMPREENDIMENTO = ?"
                params_v.append(empreendimento_id)
            
            df_v = pd.read_sql_query(query_v, conn, params=tuple(params_v))
            df_v = df_v.replace({np.nan: None})
            for col in ['DESCUNIDIMOB', 'CNPJ', 'CLIENTE_NOME', 'EMPREENDIMENTO']:
                if col in df_v.columns:
                    df_v[col] = df_v[col].map(safe_dec)
            
            vendas_dict = df_v.set_index('ID').to_dict('index')
            venda_ids = list(vendas_dict.keys())
            
            if venda_ids:
                chunk_size = 900
                for i in range(0, len(venda_ids), chunk_size):
                    chunk = venda_ids[i:i+chunk_size]
                    placeholders = ','.join('?' * len(chunk))
                    cur_sq.execute(f'''
                        SELECT prazo_id, data_venc, parcela_ref, valor, venda_id
                        FROM parcelas_abertas_projetadas
                        WHERE venda_id IN ({placeholders})
                    ''', chunk)
                    
                    for p in cur_sq.fetchall():
                        d_str = p[1]
                        val = float(p[3] or 0)
                        v_id = p[4]
                        
                        if (v_id, d_str, round(val, 2)) in assinaturas_receber:
                            continue
                            
                        if data_ini and d_str < data_ini: continue
                        if data_fim and d_str > data_fim: continue
                        
                        v_info = vendas_dict.get(v_id, {})
                        try:
                            d_fmt = pd.to_datetime(d_str).strftime('%d/%m/%Y')
                        except:
                            d_fmt = d_str
                            
                        result_list.append({
                            'id': f"prazo_{p[0]}",
                            'data': d_fmt,
                            'vencimento_iso': d_str,
                            'total': 0.0,
                            'parcela': val,
                            'variacao': 0.0,
                            'descricao_venda': v_info.get('DESCUNIDIMOB', ''),
                            'cliente_cnpj': v_info.get('CNPJ', ''),
                            'num_parcela': p[2] or '',
                            'cliente': v_info.get('CLIENTE_NOME', ''),
                            'empreendimento': v_info.get('EMPREENDIMENTO', ''),
                            'obs': 'Prevista (Em aberto - Vulcano 2.0)',
                            'desconto': 0.0,
                            'data_pagamento': '',
                            'desconto_local': 0.0,
                            'acrescimo_local': 0.0,
                            'status_sistema': 'ABERTO'
                        })
            conn_sq.close()
        except Exception as e_sq:
            print("Erro ao integrar parcelas projetadas:", e_sq)

        result_list.sort(key=lambda x: x.get('vencimento_iso') or '')

        return result_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

"""

new_content = content[:start_idx] + new_func + content[end_idx:]

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Updated successfully.')
