import os

def patch_backend():
    main_path = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py"
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update the SQL and mapping
    old_sql = "SELECT ID, NOME, CODIGOCENTROCUSTO, CONTACUSTO, CONTACLI, CONTAADICLI, CONTACAIXA, CONTAESTAND, CONTAESTCON, OBRACONCLUIDA FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ? AND ATIVO = 'S'"
    new_sql = "SELECT ID, NOME, CODIGOCENTROCUSTO, CONTACUSTO, CONTACLI, CONTAADICLI, CONTACAIXA, CONTAESTAND, CONTAESTCON, OBRACONCLUIDA, CONTAREC FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ? AND ATIVO = 'S'"
    content = content.replace(old_sql, new_sql)

    old_mapping = """                    "conta_estand": r[7], "conta_estcon": r[8], "obra_concluida": r[9]"""
    new_mapping = """                    "conta_estand": r[7], "conta_estcon": r[8], "obra_concluida": r[9], "conta_rec": r[10]"""
    content = content.replace(old_mapping, new_mapping)

    # 2. Extract the loop logic to append the new REVENUE code
    # Find the line: c_adi = emp.get("conta_adicli") or 99999
    # Add c_rec
    if 'c_adi = emp.get("conta_adicli") or 99999' in content and 'c_rec = emp.get("conta_rec") or 99999' not in content:
        content = content.replace('c_adi = emp.get("conta_adicli") or 99999', 'c_adi = emp.get("conta_adicli") or 99999\n                c_rec = emp.get("conta_rec") or 99999')

    # Find where rec_auferida_ant is calculated, and insert the DRE logic
    find_str = """                    cli_atual = min(caixa_acum, rec_auferida_atual)"""
    insert_str = """                    
                    # -----------------
                    # RECEITA DRE (Econômico)
                    mov_receita_auferida = rec_auferida_atual - rec_auferida_ant
                    logica_rec = f"Unid {uni_nome}: VGV ({vgv_uni:,.2f}) * POC ({poc_acumulado_vigente}%) = {rec_auferida_atual:,.2f} - Ant [{rec_auferida_ant:,.2f}]"
                    if abs(mov_receita_auferida) > 0.01:
                         nat_rec = 'C' if mov_receita_auferida > 0 else 'D'
                         nat_cli_rec = 'D' if mov_receita_auferida > 0 else 'C'
                         inject_virtual_entry(c_rec, abs(mov_receita_auferida), nat_rec, f"Receita Auferida (POC) - Unid {uni_nome}", logica=logica_rec, saldo_ant=-rec_auferida_ant)
                         inject_virtual_entry(c_cli, abs(mov_receita_auferida), nat_cli_rec, f"Faturamento Direito s/ Venda (POC) - Unid {uni_nome}", logica=logica_rec, saldo_ant=rec_auferida_ant)
                    # -----------------
                    
                    cli_atual = min(caixa_acum, rec_auferida_atual)"""
    
    if find_str in content and "# RECEITA DRE" not in content:
        content = content.replace(find_str, insert_str)
        
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("PATCH APPLIED SUCCESSFULLY!")

if __name__ == "__main__":
    patch_backend()
