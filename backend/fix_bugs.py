import re
import os

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update get_conn to support dynamic empresa_id FDB paths
old_get_conn = """
def get_conn(db_name="vulcano"):
    return firebirdsql.connect(
        host=FIREBIRD_HOST,
        database=DB_PATH_QUESTOR if db_name == "questor" else DB_PATH_VULCANO,
        port=FIREBIRD_PORT,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASSWORD,
        charset="WIN1252"
    )
"""

new_get_conn = """
def get_conn(db_name="vulcano", empresa_id=None):
    questor_db = DB_PATH_QUESTOR
    if db_name == "questor" and empresa_id is not None:
        import os
        base_dir = os.path.dirname(DB_PATH_QUESTOR)
        possible_path = os.path.join(base_dir, f"QUESTOR_EMPRESA_{empresa_id}.FDB")
        if os.path.exists(possible_path):
            questor_db = possible_path

    return firebirdsql.connect(
        host=FIREBIRD_HOST,
        database=questor_db if db_name == "questor" else DB_PATH_VULCANO,
        port=FIREBIRD_PORT,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASSWORD,
        charset="WIN1252"
    )
"""
content = content.replace(old_get_conn.strip(), new_get_conn.strip())

# 2. Update get_receitas_caixa to pass empresa_id to get_conn AND fix POC carry-forward logic
old_func = """@app.get("/api/receitas-caixa")
def get_receitas_caixa(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None):
    conn = get_conn("questor")"""

new_func = """@app.get("/api/receitas-caixa")
def get_receitas_caixa(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None):
    conn = get_conn("questor", empresa_id=empresa_id)"""
content = content.replace(old_func, new_func)

# Fix POC logic
old_poc_lookup = """
        # O(1) Lookup Table format agnostic (DD/MM/YYYY or YYYY-MM)
        poc_lookup = {}
        for (p_emp, val_ym), p_val in poc_map.items():
            poc_lookup[(p_emp, val_ym)] = p_val / 100.0

        # Get total VGV per Empreendimento
"""

new_poc_lookup = """
        # POC Carry-forward logic: Sort by date
        poc_list_by_emp = collections.defaultdict(list)
        for (p_emp, val_ym), p_val in poc_map.items():
            poc_list_by_emp[p_emp].append((val_ym, p_val / 100.0))
        
        for k in poc_list_by_emp:
            poc_list_by_emp[k].sort(key=lambda x: x[0])  # Sort by YYYY-MM ascending

        def get_closest_poc(emp_name, target_ym_str):
            # Encontra o último POC válido até o target_ym_str
            lst = poc_list_by_emp.get(emp_name, [])
            best_poc = 0.0
            for ym_key, val in lst:
                if ym_key <= target_ym_str:
                    best_poc = val
                else:
                    break
            return best_poc

        # Get total VGV per Empreendimento
"""
content = content.replace(old_poc_lookup.strip(), new_poc_lookup.strip())

old_poc_eval = """
            # Find closest POC for this month
            ym_str = f"{ym[0]}-{ym[1]:02d}"
            poc_pecent = poc_lookup.get((p["empreendimento"], ym_str), 0.0)
"""
new_poc_eval = """
            # Find closest POC for this month (carry-forward previous months if no measurement)
            ym_str = f"{ym[0]}-{ym[1]:02d}"
            poc_pecent = get_closest_poc(p["empreendimento"], ym_str)
"""
content = content.replace(old_poc_eval.strip(), new_poc_eval.strip())

old_ret_poc = """
            ym_str = periodo_str[:7] if periodo_str else ""
            poc_val = poc_lookup.get((emp, ym_str), 0.0)
"""
new_ret_poc = """
            ym_str = periodo_str[:7] if periodo_str else ""
            poc_val = get_closest_poc(emp, ym_str)
"""
content = content.replace(old_ret_poc.strip(), new_ret_poc.strip())

old_omission = """
        # Omissiões sem movimento
        for (poc_emp, poc_ym), poc_val in poc_lookup.items():
            # Filtro cronológico rudimentar:
"""
new_omission = """
        # Omissiões sem movimento (Injetar meses medidos no calendário fiscal)
        for poc_emp, lst in poc_list_by_emp.items():
            for poc_ym, poc_val in lst:
                # Filtro cronológico rudimentar:
"""
content = content.replace(old_omission.strip(), new_omission.strip())


with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Backend features patched!")
