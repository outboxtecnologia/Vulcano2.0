@app.get("/api/receitas-caixa")
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
        # ATENÇÃO: Somente filtramos o TETO (<= data_fim) no SQL para calcularmos os acumulados! 
        # O piso (>= data_ini) será aplicado em memória, antes de devolver à UI.
        if data_fim:
            join_conditions = " AND r.DATA <= ?"
            params.insert(0, data_fim)
            
        # Modifica o LEFT JOIN injetando o filtro de data teto para os pagamentos!
        query = query.replace("AND r.TOTALPAGO > 0", "AND r.TOTALPAGO > 0" + join_conditions)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY r.DATA DESC NULLS LAST"
        
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
        unidade_meta = collections.defaultdict(lambda: {
            "vgv": 0.0, "acrescimo_total": 0.0, "acrescimo_caixa_mes": 0.0, "caixa_acumulado": 0.0, "caixa_mes": 0.0, "tributos_caixa_acumulado": 0.0, "tributos_caixa_mes": 0.0,
            "detalhe_acumulado": {"pis": 0.0, "cofins": 0.0, "csll": 0.0, "irpj": 0.0, "ret": 0.0, "irpj_adicional": 0.0},
            "detalhe_mes": {"pis": 0.0, "cofins": 0.0, "csll": 0.0, "irpj": 0.0, "ret": 0.0, "irpj_adicional": 0.0}
        })
        
        target_ini_date = data_ini if data_ini else "1900-01-01"
        
        for r in rows:
            emp = decode_val(r[2])
            uni = str(r[3] or '').strip()
            comp = decode_val(r[4])
            
            periodo_str = decode_val(r[5])
            receita_caixa = float(r[6] or 0)
            val_parcela = float(r[7] or 0)
            val_variacao = float(r[8] or 0)
            vgv_base = float(r[9] or 0)
            is_ret = (str(r[10] or '').upper() == 'S')
            is_distrato = str(r[11]).strip().upper() == 'S' if len(r) > 11 and r[11] else False
            id_venda = r[13] if len(r) > 13 else 0
            
            vgv = 0.0 if is_distrato else vgv_base
            
            key = (emp, uni, comp, id_venda)
            
            # VGV is the same for all rows of this unit, just assign continuously
            unidade_meta[key]["vgv"] = vgv
            unidade_meta[key]["emp"] = emp
            unidade_meta[key]["uni"] = uni
            unidade_meta[key]["comprador"] = comp
            unidade_meta[key]["is_ret"] = is_ret
            
            # Acréscimo (Operational Revenue): either the explicit variação or the delta of total paid over original slip
            acrescimo = max(0, receita_caixa - val_parcela)
            if val_variacao > acrescimo:
                acrescimo = val_variacao
            unidade_meta[key]["acrescimo_total"] += acrescimo
            
            if periodo_str and receita_caixa > 0:
                try:
                    dt = datetime.datetime.strptime(periodo_str, '%Y-%m-%d')
                    ym = (dt.year, dt.month)
                except:
                    ym = (1900, 1)
                    
                if not is_ret:
                    monthly_totals[ym] += receita_caixa
                
                unidade_meta[key]["caixa_acumulado"] += receita_caixa
                if periodo_str >= target_ini_date:
                    unidade_meta[key]["caixa_mes"] += receita_caixa
                    unidade_meta[key]["acrescimo_caixa_mes"] += acrescimo
                    
                # Store dates mapping to calculate taxes later if needed
                if "recebimentos" not in unidade_meta[key]:
                    unidade_meta[key]["recebimentos"] = []
                unidade_meta[key]["recebimentos"].append((ym, receita_caixa, periodo_str))

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

        # Calculo Extendido dos Tributos da Unidade
        for key, v in unidade_meta.items():
            if "recebimentos" in v:
                for ym, caixa, periodo in v["recebimentos"]:
                    det = {"pis": 0.0, "cofins": 0.0, "csll": 0.0, "irpj": 0.0, "ret": 0.0, "irpj_adicional": 0.0}
                    if v.get("is_ret", False):
                        det["ret"] = caixa * 0.04
                        tributos_caixa_iter = det["ret"]
                    else:
                        total_m = monthly_totals.get(ym, 0)
                        fraction = (caixa / total_m) if total_m > 0 else 0
                        det["irpj_adicional"] = month_adicional.get(ym, 0) * fraction
                        det["pis"] = caixa * 0.0065
                        det["cofins"] = caixa * 0.03
                        det["irpj"] = caixa * 0.012
                        det["csll"] = caixa * 0.0108
                        tributos_caixa_iter = sum(det.values())
                        
                    v["tributos_caixa_acumulado"] += tributos_caixa_iter
                    for k_imp in det:
                        v["detalhe_acumulado"][k_imp] += det[k_imp]
                        
                    if periodo >= target_ini_date:
                        v["tributos_caixa_mes"] += tributos_caixa_iter
                        for k_imp in det:
                            v["detalhe_mes"][k_imp] += det[k_imp]

        # Get POCs
        poc_map = {}
        emp_contas_by_name = {}
        emp_lookup = {}
        try:
            cur.execute("""
                SELECT ID, NOME, CONTACLI, CONTAADICLI, CONTAREC, CONTADESPESA, CONTACAIXA, 
                       CONTAVARIACAO, CONTAESTAND, CONTAESTCON, CONTACUSTO, 
                       CONTADEVOLUCAO, CONTALUCROACUM, CONTA_ESTORNO_DEVOLUCAO, 
                       OBRACONCLUIDA
                FROM EMPREENDIMENTO
            """)
            emps_all = cur.fetchall()
            for ev in emps_all:
                emp_name_str = str(ev[1]).strip() if ev[1] else str(ev[0])
                emp_lookup[ev[0]] = emp_name_str
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
                
                # Se a obra estiver concluída ('S'), forçamos 100% de POC desde a linha do tempo inicial
                is_concluida = str(ev[14]).strip().upper() == 'S' if len(ev) > 14 and ev[14] else False
                if is_concluida:
                    # Inserimos a data base 2000-01 para garantir que qualquer target_ym bata 100%
                    poc_map[(emp_name_str, '2000-01')] = 100.0
        except Exception as e:
            cur.execute("SELECT ID, NOME, OBRACONCLUIDA FROM EMPREENDIMENTO")
            emps_all = cur.fetchall()
            for r in emps_all:
                emp_name_str = str(r[1]).strip() if r[1] else str(r[0])
                emp_lookup[r[0]] = emp_name_str
                emp_contas_by_name[emp_name_str] = {}
                # Forçamos poc=100 se concluida, igual ao bloco feliz
                is_concluida = str(r[2]).strip().upper() == 'S' if len(r) > 2 and r[2] else False
                if is_concluida:
                    poc_map[(emp_name_str, '2000-01')] = 100.0
        
        # Lê a tabela oficial POC do Vulcano
        try:
            cur.execute("SELECT ID_EMPREENDIMENTO, PERIODO, PERCENTUAL FROM POC")
            for row in cur.fetchall():
                e_id, periodo, p = row
                if not e_id or not periodo: continue
                p_str = decode_val(periodo)
                emp_name = emp_lookup.get(e_id, str(e_id))
                ym_key = p_str[:7]
                current_val = poc_map.get((emp_name, ym_key), 0.0)
                raw_p = float(p or 0)
                capped_p = raw_p if raw_p <= 100.0 else 100.0
                poc_map[(emp_name, ym_key)] = max(current_val, capped_p)
        except Exception as e:
            print("Aviso Lendo POC Oficial Vulcano:", e)

        poc_list_by_emp = collections.defaultdict(list)
        for (p_emp, val_ym), p_val in poc_map.items():
            poc_list_by_emp[p_emp].append((val_ym, p_val / 100.0))
        
        for k in poc_list_by_emp:
            poc_list_by_emp[k].sort(key=lambda x: x[0])  # Sort by YYYY-MM ascending

        def get_poc_at_or_before(emp_name, target_ym_str):
            lst = poc_list_by_emp.get(emp_name, [])
            best_poc = 0.0
            for ym_key, val in lst:
                if ym_key <= target_ym_str:
                    best_poc = val
                else:
                    break
            return best_poc

        def get_poc_strictly_before(emp_name, target_ym_str):
            lst = poc_list_by_emp.get(emp_name, [])
            best_poc = 0.0
            for ym_key, val in lst:
                if ym_key < target_ym_str:
                    best_poc = val
                else:
                    break
            return best_poc

        anchor_ym = data_fim[:7] if data_fim else datetime.datetime.now().strftime("%Y-%m")
        dashboard_meta = {}
        mapped_ret_keys = set()
        
        # Consolidation Phase
        for (emp, uni, comp, id_venda), v in unidade_meta.items():
            if emp not in dashboard_meta:
                 poc_acumulado = get_poc_at_or_before(emp, anchor_ym)
                 poc_anterior = get_poc_strictly_before(emp, anchor_ym)
                 poc_mes = max(0, poc_acumulado - poc_anterior)
                 dashboard_meta[emp] = {
                     "vgv": 0.0,
                     "poc": poc_acumulado * 100.0,
                     "poc_anterior": poc_anterior * 100.0,
                     "poc_mes": poc_mes * 100.0,
                     "receita_societaria": 0.0,
                     "receita_soc_mes": 0.0,
                     "caixa_acumulado": 0.0,
                     "caixa_mes": 0.0,
                     "tributos_caixa_acumulado": 0.0,
                     "tributos_caixa_mes": 0.0,
                     "tributos_soc_acumulado": 0.0,
                     "tributos_soc_mes": 0.0,
                     "unidades": [],
                     "contas_contabeis": emp_contas_by_name.get(emp, {})
                 }
                 
            poc_acumulado = dashboard_meta[emp]["poc"] / 100.0
            poc_mes = dashboard_meta[emp]["poc_mes"] / 100.0
            
            soc_acumulada_uni = v["vgv"] * poc_acumulado
            soc_mes_uni = v["vgv"] * poc_mes
            
            # Tax Accounting Logic
            eff_rate_acum = (v["tributos_caixa_acumulado"] / v["caixa_acumulado"]) if v["caixa_acumulado"] > 0 else 0
            eff_rate_mes = (v["tributos_caixa_mes"] / v["caixa_mes"]) if v["caixa_mes"] > 0 else 0
            
            tributos_soc_acumulada_uni = soc_acumulada_uni * eff_rate_acum
            tributos_soc_mes_uni = soc_mes_uni * eff_rate_mes
            
            dashboard_meta[emp]["vgv"] += v["vgv"]
            dashboard_meta[emp]["receita_societaria"] += soc_acumulada_uni
            dashboard_meta[emp]["receita_soc_mes"] += soc_mes_uni
            dashboard_meta[emp]["caixa_acumulado"] += v["caixa_acumulado"]
            dashboard_meta[emp]["caixa_mes"] += v["caixa_mes"]
            dashboard_meta[emp]["tributos_caixa_acumulado"] += v["tributos_caixa_acumulado"]
            dashboard_meta[emp]["tributos_caixa_mes"] += v["tributos_caixa_mes"]
            dashboard_meta[emp]["tributos_soc_acumulado"] += tributos_soc_acumulada_uni
            dashboard_meta[emp]["tributos_soc_mes"] += tributos_soc_mes_uni
            
            dashboard_meta[emp]["unidades"].append({
                "unidade": uni,
                "comprador": comp,
                "vgv": v["vgv"],
                "caixa_acumulado": v["caixa_acumulado"],
                "caixa_mes": v["caixa_mes"],
                "soc_acumulado": soc_acumulada_uni,
                "soc_mes": soc_mes_uni,
                "tributos_caixa_acumulado": v["tributos_caixa_acumulado"],
                "tributos_caixa_mes": v["tributos_caixa_mes"],
                "tributos_soc_acumulado": tributos_soc_acumulada_uni,
                "tributos_soc_mes": tributos_soc_mes_uni,
                "trib_detalhe_caixa_acumulado": dict(v["detalhe_acumulado"]),
                "trib_detalhe_caixa_mes": dict(v["detalhe_mes"])
            })
            
        # Reconstruct standard 'data' payload for legacy top-UI cards
        data = []
        for emp, meta in dashboard_meta.items():
            for u in meta["unidades"]:
                base = u["caixa_mes"]
                data.append({
                    "estabelecimento": "1",
                    "empreendimento": emp,
                    "unidade": u["unidade"],
                    "comprador": u["comprador"],
                    "periodo": anchor_ym + "-01", # Fake mid-month to pass UI isDateInRange
                    "vgv": u["vgv"],
                    "receita_caixa": base,
                    "base_calculo": base,
                    "receita_societaria": u["soc_mes"],
                    "poc": meta["poc"],
                    "pis": base * 0.0065,
                    "cofins": base * 0.03,
                    "irpj": base * 0.012,
                    "csll": base * 0.0108,
                    "ret": 0.0,
                    "tributos_total": u["tributos_caixa_mes"],
                    "tributos_societario": u["tributos_soc_mes"],
                    "saldo_clientes": max(0, u["soc_acumulado"] - u["caixa_acumulado"]),
                    "saldo_tributos": max(0, u["caixa_acumulado"] - u["soc_acumulado"]),
                    "caixa_acumulado": u["caixa_acumulado"],
                    "soc_acumulado": u["soc_acumulado"],
                    "tributos_caixa_acumulado": u["tributos_caixa_acumulado"],
                    "tributos_soc_acumulado": u["tributos_soc_acumulado"]
                })
                
        ret_consolidado = [] # Omitting mapping here for strict unit-wise handling in UI
        
        conn.close()
        return {"dashboard_data": data, "ret_consolidado": ret_consolidado, "dashboard_meta": dashboard_meta}
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))
