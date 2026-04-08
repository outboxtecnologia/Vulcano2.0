from fastapi import HTTPException

@app.get("/api/sero/maodeobra")
def api_sero_maodeobra(empresa_id: int = 959, ano: int = 2025, mes: int = 12, cno: str = None):
    conn_vulcano = get_conn("vulcano")
    conn_questor = get_conn("questor")
    
    try:
        cur_v = conn_vulcano.cursor()
        cur_q = conn_questor.cursor()
        
        # 1. Fetch Projects & Built Area (Vulcano)
        if cno:
            cur_v.execute("SELECT ID, NOME, CNO, DATACONCLUSAO, COALESCE(METRAGEMTOTAL, 0) FROM EMPREENDIMENTO WHERE CNO = ? AND CODIGOEMPRESA = ?", (cno, empresa_id))
        else:
            cur_v.execute("SELECT ID, NOME, CNO, DATACONCLUSAO, COALESCE(METRAGEMTOTAL, 0) FROM EMPREENDIMENTO WHERE CNO IS NOT NULL AND CNO <> '' AND CODIGOEMPRESA = ?", (empresa_id,))
            
        projetos = cur_v.fetchall()
        
        # 2. Fetch CUB indices
        cur_v.execute("SELECT MES, VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 ORDER BY MES ASC")
        cub_history = {str(r[0])[:7]: float(r[1]) for r in cur_v.fetchall()} # dict 'YYYY-MM' -> value
        
        # Fallback CUB if missing
        default_cub = 2850.0 
        
        area_total_calc = 0.0
        total_mao_de_obra_questor = 0.0
        total_inss_a_recolher = 0.0
        
        # Store aggregations
        historico_mensal = {} # 'YYYY-MM' -> {'realizado': 0, 'previsto': 0}
        
        # To find start date, we will just use the min period for all CNOs requested.
        data_minima = f"{ano}-12"
        data_maxima = f"{ano}-01"
        
        for proj in projetos:
            pid, pnome, pcno, pconclusao, parea = proj
            parea = float(parea) if parea else 0.0
            area_total_calc += parea
            
            # Questor Folha Calculation for this CNO
            # The CNO in Vulcano is string, let's strip formats to match Questor OUTRAEMPRESA or just raw.
            raw_cno = "".join(filter(str.isdigit, pcno))
            
            # Fetch OUTRAEMPRESA that matches this CNO
            cur_q.execute("""
                SELECT OE.CODIGOOUTEMP, OEE.INSCRFEDPROPRIET, E.NOMEESTAB
                FROM OUTRAEMPRESA OE
                LEFT JOIN OUTRAEMPEMP OEE ON OEE.CODIGOOUTEMP = OE.CODIGOOUTEMP AND OEE.CODIGOEMPRESA = ?
                LEFT JOIN ESTAB E ON E.CODIGOESTAB = OEE.CODIGOESTABPROPRIET AND E.CODIGOEMPRESA = ?
                WHERE REPLACE(REPLACE(REPLACE(OE.CGCECEIDOCF, '.', ''), '-', ''), '/', '') = ?
                OR REPLACE(REPLACE(REPLACE(OE.NOMEANTERIOR, '.', ''), '-', ''), '/', '') = ?
                OR CAST(OE.CODIGOOUTEMP AS VARCHAR(20)) = ?
            """, (empresa_id, empresa_id, raw_cno, raw_cno, raw_cno))
            
            outemp_data = cur_q.fetchone()
            if not outemp_data:
                # If cannot match specific outemp, we might just search CALCULORATEIO where outemp has the raw_cno. 
                # Let's fallback to searching the string. For simplicity we try direct numeric match if possible.
                try:
                    codigo_outemp = int(raw_cno)
                except:
                    codigo_outemp = -1
            else:
                codigo_outemp = outemp_data[0]
            
            cur_q.execute("""
                SELECT P.COMPET, SUM(C.VALOREVENTO)
                FROM CALCULORATEIO C
                JOIN PERIODOCALCULO P ON P.CODIGOPERCALCULO = C.CODIGOPERCALCULO
                WHERE C.CODIGOEVENTO = 5041 
                AND C.CODIGOEMPRESA = ?
                AND C.CODIGOOUTEMP = ?
                GROUP BY P.COMPET
            """, (empresa_id, codigo_outemp))
            
            folha_meses = cur_q.fetchall()
            
            # SERO Logic for this project 
            # (Area * CUB_MES * 20%) * 36.8%
            # We must map 48 months starting from the first folio month
            start_date_str = None
            if folha_meses:
                folha_meses.sort(key=lambda x: str(x[0]))
                start_date_str = str(folha_meses[0][0])[:7] # YYYY-MM
            else:
                start_date_str = f"{ano-4}-{str(mes).zfill(2)}"
                
            if start_date_str < data_minima: data_minima = start_date_str
            
            y_s, m_s = map(int, start_date_str.split('-'))
            
            for m_offset in range(48):
                c_m = m_s + m_offset
                c_y = y_s
                while c_m > 12:
                    c_m -= 12
                    c_y += 1
                
                comp_str = f"{c_y}-{str(c_m).zfill(2)}"
                
                # Check bounds
                if comp_str > f"{ano}-{str(mes).zfill(2)}":
                    break
                    
                if pconclusao:
                    # If project concluded and comp_str is after conclusion year-month, stop projecting Sero Estimated.
                    conc_str = str(pconclusao)[:7]
                    if comp_str > conc_str:
                        continua_projetar = False
                    else:
                        continua_projetar = True
                else:
                    continua_projetar = True
                    
                if comp_str > data_maxima: data_maxima = comp_str
                
                if comp_str not in historico_mensal:
                    historico_mensal[comp_str] = {'previsto': 0.0, 'realizado': 0.0}
                
                if continua_projetar:
                    cub_mes = cub_history.get(comp_str, default_cub)
                    # Estimativa Sero Mes a Mes: 
                    # Na vdd o SERO cobra sobre o Total da Obra, dividimos o total em 48x? 
                    # Sim, a evolução da obra é gradual.
                    fracao_estimada = (parea * cub_mes * 0.20 * 0.368) / 48.0
                    historico_mensal[comp_str]['previsto'] += fracao_estimada
            
            for (compet, val) in folha_meses:
                comp_str = str(compet)[:7]
                if comp_str not in historico_mensal:
                    historico_mensal[comp_str] = {'previsto': 0.0, 'realizado': 0.0}
                
                valor_inss = float(val) if val else 0.0
                historico_mensal[comp_str]['realizado'] += valor_inss
                total_mao_de_obra_questor += valor_inss
                
        # Consolidate LineChart
        curva_s = []
        acc_real = 0.0
        acc_prev = 0.0
        for m in sorted(historico_mensal.keys()):
            if m < data_minima or m > data_maxima: continue
            
            acc_real += historico_mensal[m]['realizado']
            acc_prev += historico_mensal[m]['previsto']
            
            curva_s.append({
                "mes": m,
                "realizado_mes": round(historico_mensal[m]['realizado'], 2),
                "previsto_mes": round(historico_mensal[m]['previsto'], 2),
                "realizado": round(acc_real, 2),
                "previsto": round(acc_prev, 2)
            })
            
        total_inss_a_recolher = acc_prev - acc_real
        if total_inss_a_recolher < 0: total_inss_a_recolher = 0

        # Latest CUB
        cub_target = cub_history.get(f"{ano}-{str(mes).zfill(2)}", default_cub)

        return {
            "resumo": {
                "mao_de_obra": total_mao_de_obra_questor,
                "total_inss": total_inss_a_recolher,
                "cub_vigente": cub_target,
                "area_total": area_total_calc
            },
            "curva_s": curva_s
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn_vulcano.close()
        conn_questor.close()
