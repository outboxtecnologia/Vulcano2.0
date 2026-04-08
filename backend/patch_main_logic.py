import os

NEW_LOGIC = """
            nome_emp = emp["nome"]
            
            # 1. OBTER CUSTO GASTO GLOBAL NA CONTABILIDADE FÍSICA (QUESTOR)
            custo_gasto_vigente = 0.0
            custo_gasto_anterior = 0.0
            for conta, dt_contabil in contas_fisicas.items():
                # O saldo das contas de Custo no Questor reflete o total gasto.
                custo_gasto_anterior += dt_contabil["saldo_anterior"]
                custo_gasto_vigente += dt_contabil["saldo_final"]

            # 2. POC NATIVO (Reaproveitando Último Fechamento se não houver no mês)
            poc_acumulado_vigente = 0.0
            poc_acumulado_anterior = 0.0
            ob_concluida = str(emp.get("obra_concluida", "N")).strip().upper() == 'S'
            if ob_concluida:
                poc_acumulado_vigente = 100.0
                poc_acumulado_anterior = 100.0
            else:
                try:
                    cur_v.execute("SELECT PERIODO, PERCENTUAL FROM POC WHERE ID_EMPREENDIMENTO = ?", (emp["id"],))
                    pocs_raw = cur_v.fetchall()
                    
                    target_per = f"{str(ano).zfill(4)}-{str(mes).zfill(2)}"
                    pocs_valid = []
                    for (per, pct) in pocs_raw:
                        if not per: continue
                        a, m = 0, 0
                        per_str = str(per).strip()
                        if '/' in per_str:
                            parts = per_str.split('/')
                            if len(parts) == 2: a, m = int(parts[1]), int(parts[0])
                            elif len(parts) == 3: a, m = int(parts[2]), int(parts[1])
                        elif '-' in per_str:
                            parts = per_str.split('-')
                            if len(parts) >= 2: a, m = int(parts[0]), int(parts[1])
                        
                        if a > 0 and m > 0:
                            std_per = f"{str(a).zfill(4)}-{str(m).zfill(2)}"
                            pocs_valid.append((std_per, float(pct or 0)))
                    
                    pocs_valid.sort(key=lambda x: x[0])
                    last_poc = 0.0
                    for (p, pct) in pocs_valid:
                        if p < target_per:
                            poc_acumulado_anterior = pct
                            last_poc = pct
                        if p <= target_per:
                            poc_acumulado_vigente = pct
                            last_poc = pct
                    
                    # Carry forward se não houver atualização no mês alvo
                    if poc_acumulado_vigente == 0.0 and last_poc > 0.0:
                        poc_acumulado_vigente = last_poc
                        poc_acumulado_anterior = last_poc
                except Exception as e:
                    print("Erro lendo POC Nativo:", e)

            # 3. RATEIO UNIDADE A UNIDADE (CUSTO, RECEBIMENTOS, E TRIBUTOS)
            meta_emp = receitas_meta.get(nome_emp, {})
            if meta_emp:
                vgv_global = meta_emp.get("vgv", 0.0) or 1.0
                unidades = meta_emp.get("unidades", [])
                
                c_custo = emp.get("conta_custo") or 99999
                c_estcon = emp.get("conta_estcon") if ob_concluida else emp.get("conta_estand")
                c_estoque = c_estcon if c_estcon else 99999
                
                c_caixa_banco = emp.get("conta_caixa") or 99999
                c_cli = emp.get("conta_cli") or 99999
                c_adi = emp.get("conta_adicli") or 99999
                
                # Identifica se é lucro presumido com RET
                ret_global = meta_emp.get("ret", 0)
                pis_cofins_global = meta_emp.get("pis", 0) + meta_emp.get("cofins", 0)
                isRet = ret_global > 0 and pis_cofins_global == 0
                valid_confs = [c for c in impostos_config if c.get("RET") == ("S" if isRet else "N")]
                
                for uni_data in unidades:
                    uni_nome = uni_data["unidade"]
                    vgv_uni = uni_data["vgv"]
                    if vgv_uni <= 0: continue
                    
                    # CUSTO ECONÔMICO (Apenas unidades vendidas)
                    rateio_venda = vgv_uni / vgv_global
                    custo_u_atual = custo_gasto_vigente * rateio_venda * (poc_acumulado_vigente / 100.0)
                    custo_u_ant = custo_gasto_anterior * rateio_venda * (poc_acumulado_anterior / 100.0)
                    mov_custo_u = custo_u_atual - custo_u_ant
                    
                    if abs(mov_custo_u) > 0.01:
                         logica_custo = f"Unid {uni_nome}: Custo Acum CC ({custo_gasto_vigente:,.2f}) * Peso VGV ({rateio_venda*100:.2f}%) * POC ({poc_acumulado_vigente}%) = {custo_u_atual:,.2f} - Ant [{custo_u_ant:,.2f}]"
                         inject_virtual_entry(c_custo, mov_custo_u, 'D', f"Custo POC - Unid {uni_nome}", logica=logica_custo, saldo_ant=custo_u_ant)
                         inject_virtual_entry(c_estoque, mov_custo_u, 'C', f"Contrapartida RecCusto POC - Unid {uni_nome}", logica=logica_custo, saldo_ant=-custo_u_ant)

                    # RECEBIMENTOS E RATEIO PASSSIVO
                    caixa_m = uni_data["caixa_mes"]
                    if caixa_m > 0:
                         logica_caixa = f"Unid {uni_nome}: Recebimento Mês = {caixa_m:,.2f}"
                         inject_virtual_entry(c_caixa_banco, caixa_m, 'D', f"Recebimento Caixa - Unid {uni_nome}", logica=logica_caixa, saldo_ant=0.0)

                    caixa_acum = uni_data["caixa_acumulado"]
                    caixa_ant = caixa_acum - caixa_m
                    
                    rec_auferida_atual = vgv_uni * (poc_acumulado_vigente / 100.0)
                    rec_auferida_ant = vgv_uni * (poc_acumulado_anterior / 100.0)
                    
                    cli_atual = min(caixa_acum, rec_auferida_atual)
                    adi_atual = max(0, caixa_acum - rec_auferida_atual)
                    
                    cli_ant = min(caixa_ant, rec_auferida_ant)
                    adi_ant = max(0, caixa_ant - rec_auferida_ant)
                    
                    mov_cli = cli_atual - cli_ant
                    mov_adi = adi_atual - adi_ant
                    logica_cli = f"Unid {uni_nome}: Limite POC = {rec_auferida_atual:,.2f}. CAIXA = {caixa_acum:,.2f}."
                    
                    if abs(mov_cli) > 0.01:
                         nat_cli = 'C' if mov_cli > 0 else 'D'
                         inject_virtual_entry(c_cli, abs(mov_cli), nat_cli, f"Variação Clientes - Unid {uni_nome}", logica=logica_cli, saldo_ant=-cli_ant)
                    
                    if abs(mov_adi) > 0.01:
                         nat_adi = 'C' if mov_adi > 0 else 'D'
                         inject_virtual_entry(c_adi, abs(mov_adi), nat_adi, f"Variação Adiantamento - Unid {uni_nome}", logica=logica_cli, saldo_ant=-adi_ant)
                         
                    # TRIBUTOS
                    trib_caixa_atual = uni_data["tributos_caixa_acumulado"]
                    trib_caixa_ant = trib_caixa_atual - uni_data["tributos_caixa_mes"]
                    
                    trib_soc_atual = uni_data["tributos_soc_acumulado"]
                    trib_soc_ant = trib_soc_atual - uni_data["tributos_soc_mes"]
                    
                    t_dif_atual = max(0, trib_soc_atual - trib_caixa_atual)
                    t_dif_ant = max(0, trib_soc_ant - trib_caixa_ant)
                    mov_dif = t_dif_atual - t_dif_ant
                    
                    t_ant_atual = max(0, trib_caixa_atual - trib_soc_atual)
                    t_ant_ant = max(0, trib_caixa_ant - trib_soc_ant)
                    mov_ant = t_ant_atual - t_ant_ant
                    
                    trib_det_mes = uni_data.get("trib_detalhe_caixa_mes", {})
                    
                    for cfg in valid_confs:
                        desc = cfg.get("DESCRICAO", "")
                        
                        # Pegamos o valor exato no mês (financeiro base caixa) para esse imposto específico
                        if desc == 'RET': bVal = trib_det_mes.get("ret", 0)
                        elif desc == 'PIS': bVal = trib_det_mes.get("pis", 0)
                        elif desc == 'COFINS': bVal = trib_det_mes.get("cofins", 0)
                        elif desc == 'CSLL': bVal = trib_det_mes.get("csll", 0)
                        elif desc == 'IRPJ': bVal = trib_det_mes.get("irpj", 0)
                        elif desc == 'IRPJ Adicional': bVal = trib_det_mes.get("irpj_adicional", 0)
                        else: bVal = 0

                        # Qual peso desse imposto na carga tributária toda da unidade?
                        peso_imp = bVal / uni_data["tributos_caixa_mes"] if uni_data["tributos_caixa_mes"] > 0 else (1.0 / len(valid_confs) if valid_confs else 1.0)
                        if bVal <= 0 and mov_dif <= 0 and mov_ant <= 0: continue
                        
                        logica_imp = f"Unid {uni_nome}: Trib Caixa ({trib_caixa_atual:,.2f}) vs Trib DRE ({trib_soc_atual:,.2f}). Peso {desc}: {peso_imp*100:.1f}%"
                        
                        m_dif = mov_dif * peso_imp
                        m_ant = mov_ant * peso_imp
                        
                        # Diferido (A pagar no futuro pq DRE andou mas não geramos caixa)
                        if abs(m_dif) > 0.01:
                            c_deb = cfg.get("CONTA_DEB_IMP_APROP_ATIVO") or 99999
                            c_cred = cfg.get("CONTA_CRED_IMP_REC_PASSIVO_SOC") or 99999
                            nat_d = 'D' if m_dif > 0 else 'C'
                            nat_c = 'C' if m_dif > 0 else 'D'
                            inject_virtual_entry(c_deb, abs(m_dif), nat_d, f"Provisão Tributo Diferido - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=0)
                            inject_virtual_entry(c_cred, abs(m_dif), nat_c, f"Passivo Tributo Diferido - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=0)
                            
                        # Antecipado (Pago hoje, mas DRE ainda não auferiu pq POC baixo)
                        if abs(m_ant) > 0.01:
                            c_deb = cfg.get("CONTA_DEB_IMP_SOBRE_VENDA_VARIA") or 99999
                            c_cred = cfg.get("CONTA_CRED_IMP_REC_DARF_VARIA") or 99999
                            nat_d = 'D' if m_ant > 0 else 'C'
                            nat_c = 'C' if m_ant > 0 else 'D'
                            inject_virtual_entry(c_deb, abs(m_ant), nat_d, f"Tributo Antecipado (Ativo) - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=0)
                            inject_virtual_entry(c_cred, abs(m_ant), nat_c, f"Constituição Adiant Trib - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=0)
                            
                        # Despesa Direta sobre a Receita Real Auferida Mês (A que vai pra DRE)
                        despesa_dre_mes_imp = (trib_soc_atual - trib_soc_ant) * peso_imp
                        if abs(despesa_dre_mes_imp) > 0.01:
                            c_deb = cfg.get("CONTA_DEB_IMP_SOBRE_VENDA_VARIA") or 99999
                            c_cred = cfg.get("CONTA_CRED_IMP_REC_DARF_VARIA") or 99999
                            nat_d = 'D' if despesa_dre_mes_imp > 0 else 'C'
                            nat_c = 'C' if despesa_dre_mes_imp > 0 else 'D'
                            logica_dre = f"Unid {uni_nome}: PIS/COF na DRE. Base Econômica POC [{desc}]"
                            inject_virtual_entry(c_deb, abs(despesa_dre_mes_imp), nat_d, f"Despesa Tributária DRE - {desc} Unid {uni_nome}", logica=logica_dre, saldo_ant=0)
                            inject_virtual_entry(c_cred, abs(despesa_dre_mes_imp), nat_c, f"Baixa DARF/Passivo - {desc} Unid {uni_nome}", logica=logica_dre, saldo_ant=0)
"""

def patch_backend():
    main_path = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py"
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_str = '            nome_emp = emp["nome"]'
    end_str = '            # --- GARANTIR QUE CONTAS COM SALDO ANTERIOR APAREÇAM (Não Zerem) ---'
    
    idx_start = content.find(start_str)
    idx_end = content.find(end_str)
    
    if idx_start == -1 or idx_end == -1:
        print("MARCADOR REJECTED!")
        return
        
    final_content = content[:idx_start] + NEW_LOGIC + content[idx_end:]
    
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print("PATCH APPLIED SUCCESSFULLY!")
        
if __name__ == "__main__":
    patch_backend()
