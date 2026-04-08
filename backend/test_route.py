from main import api_custos_dashboard_by_id
try:
    print(api_custos_dashboard_by_id(id_emp=5, mes=12, ano=2024))
except Exception as e:
    import traceback
    with open('exception_dump.txt', 'w') as f:
        f.write(traceback.format_exc())
    print("CRASHED!")
