import re

filepath = "main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace POC logic: Remove POC_CUSTOS, read ONLY POC.
poc_code = """
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
            raw_p = float(p or 0)
            capped_p = raw_p if raw_p <= 100.0 else 100.0
            poc_map[(emp_name, ym_key)] = max(current_val, capped_p)
            
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
"""

poc_new_code = """
        # Get POCs
        poc_map = {}
        cur.execute("SELECT ID, NOME FROM EMPREENDIMENTO")
        emp_lookup = {r[0]: str(r[1]).strip() if r[1] else "" for r in cur.fetchall()}
        
        # Lê apenas a tabela POC manual
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
"""
content = content.replace(poc_code.strip(), poc_new_code.strip())

data_loop = """
        data = []
        ret_consolidado = []
        mapped_ret_keys = set()
"""

data_new = """
        data = []
        ret_consolidado = []
        mapped_ret_keys = set()
        
        anchor_ym = data_fim[:7] if data_fim else datetime.datetime.now().strftime("%Y-%m")
        dashboard_meta = {}
        
        for emp, vgv in vgv_por_empreendimento.items():
            poc_pecent = get_closest_poc(emp, anchor_ym)
            receita_societaria = vgv * poc_pecent
            dashboard_meta[emp] = {
                "vgv": vgv,
                "poc": poc_pecent * 100.0,
                "receita_societaria": receita_societaria
            }
"""
content = content.replace(data_loop.strip(), data_new.strip())


receita_societaria = """
            # --- SOCIETARY ---
            ym_str = f"{ym[0]}-{ym[1]:02d}"
            poc_pecent = get_closest_poc(emp, ym_str)
            receita_societaria = p["vgv"] * poc_pecent
"""
receita_societaria_new = """
            # --- SOCIETARY ---
            # Receita Societaria por recibo é mitigada, controlada globalmente no metadata.
            receita_societaria = 0.0
"""
content = content.replace(receita_societaria.strip(), receita_societaria_new.strip())

return_statement = "return {\"dashboard_data\": data, \"ret_consolidado\": ret_consolidado}"
return_new = "return {\"dashboard_data\": data, \"ret_consolidado\": ret_consolidado, \"dashboard_meta\": dashboard_meta}"
content = content.replace(return_statement, return_new)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Main patched for new POC rules!")
