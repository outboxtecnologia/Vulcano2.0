import re

filepath = "main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Locate the function exactly
start_str = '@app.get("/api/receitas-caixa")'
end_str = '@app.get("/api/compare/pessoas")'

idx_start = content.find(start_str)
idx_end = content.find(end_str)

if idx_start == -1 or idx_end == -1:
    print("Function boundaries not found.")
    exit(1)

new_func = '''@app.get("/api/receitas-caixa")
def get_receitas_caixa(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None):
    conn = get_conn("questor")
    cur = conn.cursor()

    query = """
    SELECT 
        v.CODIGOEMPRESA,
        v.CODIGOESTAB,
        i.IDENTEMP, 
        i.DESCUNIDIMOB, 
        i.CPFCNPJADQU, 
        v.COMPRECEB, 
        v.VLTOTREC, 
        v.VLBC, 
        v.VLPIS, 
        v.VLCOFINS,
        v.VLTOTVEND
    FROM EFDUNIDIMOBVENDIDA v
    JOIN EFDUNIDIMOBILIARIA i ON v.CODIGOEMPRESA = i.CODIGOEMPRESA AND v.CODIGOESTAB = i.CODIGOESTAB AND v.NUMCADIMOB = i.NUMCADIMOB
    {where_empresa}
    ORDER BY v.COMPRECEB DESC
    """
    try:
        conditions = []
        params = []
        if empresa_id is not None:
            conditions.append("v.CODIGOEMPRESA = ?")
            params.append(int(empresa_id))
        if data_ini:
            conditions.append("v.COMPRECEB >= ?")
            params.append(data_ini)
        if data_fim:
            conditions.append("v.COMPRECEB <= ?")
            params.append(data_fim)
            
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        cur.execute(query.format(where_empresa=where_clause), tuple(params))
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
            periodo_str = decode_val(r[4])
            try:
                dt = datetime.datetime.strptime(periodo_str, '%Y-%m-%d')
                ym = (dt.year, dt.month)
            except:
                ym = (1900, 1)
                
            base_calc = float(r[6] or 0)
            monthly_totals[ym] += base_calc
            
            parsed_rows.append({
                "raw": r,
                "ym": ym,
                "base_calc": base_calc,
                "empresa_id": r[0],
                "estabelecimento": r[1],
                "empreendimento": decode_val(r[2]),
                "unidade": decode_val(r[3]),
                "comprador": decode_val(r[4]),
                "periodo": periodo_str,
                "receita_caixa": float(r[6] or 0),
                "vgv": float(r[10] or 0)
            })

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

        # Get POCs from Vulcano Base
        poc_map = {}
        conn_vulc = get_conn("vulcano")
        c_vulc = conn_vulc.cursor()
        try:
            c_vulc.execute("SELECT ID, NOME FROM EMPREENDIMENTO")
            emp_lookup = {r[0]: str(r[1]).strip() if r[1] else "" for r in c_vulc.fetchall()}
            
            c_vulc.execute("SELECT ID_EMPREENDIMENTO, MES, ANO, PERCENTUAL_CONCLUIDO FROM POC_CUSTOS")
            for row in c_vulc.fetchall():
                e_id, m, a, p = row
                if not e_id or not a or not m: continue
                emp_name = emp_lookup.get(e_id, str(e_id))
                ym_key = f"{a}-{str(m).zfill(2)}"
                poc_map[(emp_name, ym_key)] = float(p or 0)
                
            c_vulc.execute("SELECT ID_EMPREENDIMENTO, PERIODO, PERCENTUAL FROM POC")
            for row in c_vulc.fetchall():
                e_id, periodo, p = row
                if not e_id or not periodo: continue
                p_str = decode_val(periodo)
                emp_name = emp_lookup.get(e_id, str(e_id))
                ym_key = p_str[:7]
                if (emp_name, ym_key) not in poc_map:
                    poc_map[(emp_name, ym_key)] = float(p or 0)
        except Exception as e:
            print(f"Erro POC Vulcano: {e}")
        finally:
            conn_vulc.close()
        
        # O(1) Lookup Table format agnostic (DD/MM/YYYY or YYYY-MM)
        poc_lookup = {}
        for (p_emp, val_ym), p_val in poc_map.items():
            poc_lookup[(p_emp, val_ym)] = p_val / 100.0

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
        for p in parsed_rows:
            base = p["base_calc"]
            ym = p["ym"]
            total_m = monthly_totals.get(ym, 0)
            fraction = (base / total_m) if total_m > 0 else 0
            
            adicional_unit = month_adicional.get(ym, 0) * fraction
            irpj_calc = (base * 0.012) + adicional_unit
            csll_calc = base * 0.0108
            
            pis_db = float(p["raw"][8] or 0)
            cofins_db = float(p["raw"][9] or 0)
            tributos_caixa = pis_db + cofins_db + irpj_calc + csll_calc
            
            # Societary Calculation
            vgv = p["vgv"]
            # Find closest POC for this month
            ym_str = f"{ym[0]}-{ym[1]:02d}"
            poc_pecent = poc_lookup.get((p["empreendimento"], ym_str), 0.0)
            receita_societaria = vgv * poc_pecent
            
            # Tax allocation derived from Caixa effective rate
            eff_rate = tributos_caixa / base if base > 0 else 0
            tributos_societario = receita_societaria * eff_rate
            
            saldo_clientes = base - receita_societaria
            saldo_tributos = tributos_caixa - tributos_societario
            
            data.append({
                "estabelecimento": p["estabelecimento"],
                "empreendimento": p["empreendimento"],
                "unidade": p["unidade"],
                "comprador": p["comprador"],
                "periodo": p["periodo"],
                "vgv": vgv,
                "receita_caixa": p["receita_caixa"],
                "base_calculo": base,
                "receita_societaria": receita_societaria,
                "poc": poc_pecent * 100,
                "pis": pis_db,
                "cofins": cofins_db,
                "irpj": irpj_calc,
                "csll": csll_calc,
                "tributos_total": tributos_caixa,
                "tributos_societario": tributos_societario,
                "saldo_clientes": saldo_clientes,
                "saldo_tributos": saldo_tributos
            })
        
        ret_consolidado = []
        mapped_ret_keys = set()
        
        query_ret = "SELECT CODIGOESTAB, INCIMOB, DATALCTOFIS, BCRET, ALIQRET, VLRECUNI FROM EFDINCORPIMOBRET"
        ret_conds = []
        ret_params = []
        if empresa_id is not None:
            ret_conds.append("CODIGOEMPRESA = ?")
            ret_params.append(int(empresa_id))
        if data_ini:
            ret_conds.append("DATALCTOFIS >= ?")
            ret_params.append(data_ini)
        if data_fim:
            ret_conds.append("DATALCTOFIS <= ?")
            ret_params.append(data_fim)
            
        if ret_conds:
            query_ret += " WHERE " + " AND ".join(ret_conds)
        query_ret += " ORDER BY DATALCTOFIS DESC"
        
        cur.execute(query_ret, tuple(ret_params))
        ret_rows = cur.fetchall()
        for r in ret_rows:
            emp = decode_val(r[1])
            periodo_str = decode_val(r[2]) if r[2] else ""
            
            ym_str = periodo_str[:7] if periodo_str else ""
            poc_val = poc_lookup.get((emp, ym_str), 0.0)
            
            vgv_emp = vgv_por_empreendimento.get(emp, 0.0)
            receita_societaria = vgv_emp * poc_val
            aliquota = float(r[4] or 0)
            tributos_societario = receita_societaria * (aliquota / 100.0)
            
            base_calc = float(r[3] or 0)
            imposto_caixa = float(r[5] or 0)
            
            saldo_clientes = base_calc - receita_societaria
            # para RET o ICMS/PIS etc é consolidado no DARF unico que lemos de VLRECUNI, assumindo 0 saldo tribal por un simplification?
            # Ou mantemos:
            mapped_ret_keys.add((emp, ym_str))
            
            ret_consolidado.append({
                "estabelecimento": r[0],
                "empreendimento": emp,
                "periodo": periodo_str,
                "base_calculo": base_calc,
                "aliquota": aliquota,
                "valor_ret": imposto_caixa,
                "poc": poc_val * 100,
                "receita_societaria": receita_societaria,
                "tributos_societario": tributos_societario,
                "saldo_clientes": saldo_clientes,
                "saldo_tributos": imposto_caixa - tributos_societario
            })
            
        # Omissiões sem movimento
        for (poc_emp, poc_ym), poc_val in poc_lookup.items():
            # Filtro cronológico rudimentar:
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
                        "aliquota": 4.0,  # Padrao RET
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

print("SUCESSO!")
