import re

filepath = "main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

start_str = '@app.get("/api/receitas-caixa")'
end_str = '@app.get("/api/compare/pessoas")'

idx_start = content.find(start_str)
idx_end = content.find(end_str)

if idx_start == -1 or idx_end == -1:
    print("Function boundaries not found.")
    exit(1)

new_func = '''@app.get("/api/receitas-caixa")
def get_receitas_caixa(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None):
    # Conexão agora é 100% Vulcano para abrir TODAS AS EMPRESAS!
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
        v.TOTALVENDA AS VGV,
        e.RET
    FROM RECEBER r
    JOIN VENDA v ON r.IDVENDA = v.ID
    JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
    LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
    WHERE r.TOTALPAGO > 0
    """
    
    try:
        conditions = []
        params = []
        if empresa_id is not None:
            conditions.append("v.CODIGOEMPRESA = ?")
            params.append(int(empresa_id))
        if data_ini:
            conditions.append("r.DATA >= ?")
            params.append(data_ini)
        if data_fim:
            conditions.append("r.DATA <= ?")
            params.append(data_fim)
            
        if conditions:
            query += " AND " + " AND ".join(conditions)
            
        query += " ORDER BY r.DATA DESC"
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        
        import collections
        import datetime
        
        def decode_val(val):
            if isinstance(val, datetime.date) or hasattr(val, 'strftime'):
                return val.strftime('%Y-%m-%d')
            if isinstance(val, bytes):
                try:
                    return val.decode('win1252', 'ignore').strip()
                except:
                    return str(val)
            if isinstance(val, str):
                return val.strip()
            return val

        monthly_totals = collections.defaultdict(float)
        parsed_rows = []
        
        for r in rows:
            periodo_str = decode_val(r[5])
            try:
                dt = datetime.datetime.strptime(periodo_str, '%Y-%m-%d')
                ym = (dt.year, dt.month)
            except:
                ym = (1900, 1)
                
            base_calc = float(r[6] or 0)
            
            is_ret = (str(r[8] or '').upper() == 'S')
            
            # Não soma a base das construtoras RET para apurar IRPJ Adicional
            if not is_ret:
                monthly_totals[ym] += base_calc
            
            parsed_rows.append({
                "ym": ym,
                "base_calc": base_calc,
                "empresa_id": r[0],
                "estabelecimento": r[1],
                "empreendimento": decode_val(r[2]),
                "unidade": str(r[3] or '').strip(),
                "comprador": decode_val(r[4]),
                "periodo": periodo_str,
                "receita_caixa": float(r[6] or 0),
                "vgv": float(r[7] or 0),
                "is_ret": is_ret
            })

        # --- ADICIONAL DE IRPJ ---
        quarters_data = collections.defaultdict(list)
        for ym in monthly_totals.keys():
            yq = (ym[0], (ym[1] - 1) // 3 + 1)
            if ym not in quarters_data[yq]:
                quarters_data[yq].append(ym)
                
        month_adicional = {}
        for yq, months in quarters_data.items():
            month3 = (yq[0], yq[1] * 3)
            month1 = (yq[0], yq[1] * 3 - 2)
            month2 = (yq[0], yq[1] * 3 - 1)
            
            quarter_base = monthly_totals.get(month1, 0) + monthly_totals.get(month2, 0) + monthly_totals.get(month3, 0)
            quarter_adicional = max(0, (quarter_base * 0.08) - 60000) * 0.10
            
            m1_adicional = max(0, (monthly_totals.get(month1, 0) * 0.08) - 20000) * 0.10
            m2_adicional = max(0, (monthly_totals.get(month2, 0) * 0.08) - 20000) * 0.10
            m3_adicional = quarter_adicional - m1_adicional - m2_adicional
            
            month_adicional[month1] = m1_adicional
            month_adicional[month2] = m2_adicional
            month_adicional[month3] = m3_adicional

        # Get POCs
        poc_map = {}
        cur.execute("SELECT ID, NOME FROM EMPREENDIMENTO")
        emp_lookup = {r[0]: str(r[1]).strip() if r[1] else "" for r in cur.fetchall()}
        
        cur.execute("SELECT ID_EMPREENDIMENTO, MES, ANO, PERCENTUAL_CONCLUIDO FROM POC_CUSTOS")
        for row in cur.fetchall():
            e_id, m, a, p = row
            if not e_id or not a or not m: continue
            emp_name = emp_lookup.get(e_id, str(e_id))
            ym_key = f"{a}-{str(m).zfill(2)}"
            current_val = poc_map.get((emp_name, ym_key), 0.0)
            poc_map[(emp_name, ym_key)] = max(current_val, float(p or 0))
            
        cur.execute("SELECT ID_EMPREENDIMENTO, PERIODO, PERCENTUAL FROM POC")
        for row in cur.fetchall():
            e_id, periodo, p = row
            if not e_id or not periodo: continue
            p_str = decode_val(periodo)
            emp_name = emp_lookup.get(e_id, str(e_id))
            ym_key = p_str[:7]
            current_val = poc_map.get((emp_name, ym_key), 0.0)
            poc_map[(emp_name, ym_key)] = max(current_val, float(p or 0))

        poc_list_by_emp = collections.defaultdict(list)
        for (p_emp, val_ym), p_val in poc_map.items():
            poc_list_by_emp[p_emp].append((val_ym, p_val / 100.0))
        
        for k in poc_list_by_emp:
            poc_list_by_emp[k].sort(key=lambda x: x[0])  # Sort by YYYY-MM ascending

        def get_closest_poc(emp_name, target_ym_str):
            lst = poc_list_by_emp.get(emp_name, [])
            best_poc = 0.0
            for ym_key, val in lst:
                if ym_key <= target_ym_str:
                    best_poc = val
                else:
                    break
            return best_poc

        # Get total VGV per Empreendimento
        unidades_vgv = {}
        for p in parsed_rows:
            key = (p["empreendimento"], p["unidade"], p["comprador"])
            current_vgv = unidades_vgv.get(key, 0)
            unidades_vgv[key] = max(current_vgv, p["vgv"])
        
        vgv_por_empreendimento = collections.defaultdict(float)
        for (emp, uni, comp), vgv in unidades_vgv.items():
            if emp:
                vgv_por_empreendimento[emp] += vgv

        data = []
        ret_consolidado = []
        mapped_ret_keys = set()
        
        for p in parsed_rows:
            base = p["base_calc"]
            ym = p["ym"]
            emp = p["empreendimento"]
            is_ret = p["is_ret"]
            
            # --- TRIBUTOS ---
            if is_ret:
                pis_db = 0.0
                cofins_db = 0.0
                irpj_calc = 0.0
                csll_calc = 0.0
                ret_calc = base * 0.04
            else:
                total_m = monthly_totals.get(ym, 0)
                fraction = (base / total_m) if total_m > 0 else 0
                adicional_unit = month_adicional.get(ym, 0) * fraction
                
                pis_db = base * 0.0065
                cofins_db = base * 0.03
                irpj_calc = (base * 0.012) + adicional_unit
                csll_calc = base * 0.0108
                ret_calc = 0.0
                
            tributos_caixa = pis_db + cofins_db + irpj_calc + csll_calc + ret_calc
            
            # --- SOCIETARY ---
            ym_str = f"{ym[0]}-{ym[1]:02d}"
            poc_pecent = get_closest_poc(emp, ym_str)
            receita_societaria = p["vgv"] * poc_pecent
            
            eff_rate = tributos_caixa / base if base > 0 else 0
            tributos_societario = receita_societaria * eff_rate
            
            saldo_clientes = base - receita_societaria
            saldo_tributos = tributos_caixa - tributos_societario
            
            data.append({
                "estabelecimento": p["estabelecimento"],
                "empreendimento": emp,
                "unidade": p["unidade"],
                "comprador": p["comprador"],
                "periodo": p["periodo"],
                "vgv": p["vgv"],
                "receita_caixa": p["receita_caixa"],
                "base_calculo": base,
                "receita_societaria": receita_societaria,
                "poc": poc_pecent * 100,
                "pis": pis_db,
                "cofins": cofins_db,
                "irpj": irpj_calc,
                "csll": csll_calc,
                "ret": ret_calc,
                "tributos_total": tributos_caixa,
                "tributos_societario": tributos_societario,
                "saldo_clientes": saldo_clientes,
                "saldo_tributos": saldo_tributos
            })
            
            # Popular Ret Consolidado (Legado para não quebrar UI superior)
            if is_ret:
                ret_consolidado.append({
                    "estabelecimento": p["estabelecimento"],
                    "empreendimento": emp,
                    "periodo": p["periodo"],
                    "base_calculo": base,
                    "aliquota": 4.0,
                    "valor_ret": ret_calc,
                    "poc": poc_pecent * 100,
                    "receita_societaria": receita_societaria,
                    "tributos_societario": tributos_societario,
                    "saldo_clientes": saldo_clientes,
                    "saldo_tributos": saldo_tributos
                })
                mapped_ret_keys.add((emp, ym_str))

        # Omissiões sem movimento
        for poc_emp, lst in poc_list_by_emp.items():
            for poc_ym, poc_val in lst:
                crono_check_ym = True
                if data_ini and poc_ym < data_ini[:7]: crono_check_ym = False
                if data_fim and poc_ym > data_fim[:7]: crono_check_ym = False
                
                if crono_check_ym and (poc_emp, poc_ym) not in mapped_ret_keys:
                    vgv_emp = vgv_por_empreendimento.get(poc_emp, 0.0)
                    if vgv_emp > 0:
                        receita_societaria = vgv_emp * poc_val
                        ret_consolidado.append({
                            "estabelecimento": "1",
                            "empreendimento": poc_emp,
                            "periodo": f"{poc_ym}-01",
                            "base_calculo": 0.0,
                            "aliquota": 4.0,
                            "valor_ret": 0.0,
                            "poc": poc_val * 100,
                            "receita_societaria": receita_societaria,
                            "tributos_societario": receita_societaria * 0.04,
                            "saldo_clientes": 0.0 - receita_societaria,
                            "saldo_tributos": 0.0 - (receita_societaria * 0.04)
                        })
        
        conn.close()
        return {"dashboard_data": data, "ret_consolidado": ret_consolidado}
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

'''

new_content = content[:idx_start] + new_func + content[idx_end:]
with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("SUCESSO VULCANO!")
