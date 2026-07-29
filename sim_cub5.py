import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn
import calendar

HISTORICO_BASE = {
    # 2024
    "2024-04": 2950.40, "2024-03": 2915.30, "2024-02": 2890.20, "2024-01": 2870.12,
    # 2023
    "2023-12": 2855.10, "2023-11": 2840.90, "2023-10": 2825.80, "2023-09": 2810.70,
    "2023-08": 2795.50, "2023-07": 2780.15, "2023-06": 2765.40, "2023-05": 2745.20,
    "2023-04": 2725.10, "2023-03": 2710.60, "2023-02": 2695.45, "2023-01": 2685.30,
    # 2022
    "2022-12": 2675.10, "2022-11": 2665.90, "2022-10": 2645.80, "2022-09": 2625.60,
    "2022-08": 2605.30, "2022-07": 2585.10, "2022-06": 2560.40, "2022-05": 2530.15,
    "2022-04": 2505.80, "2022-03": 2485.45, "2022-02": 2470.30, "2022-01": 2450.10,
    # 2021
    "2021-12": 2435.40, "2021-11": 2415.20, "2021-10": 2390.10, "2021-09": 2365.80,
    "2021-08": 2340.65, "2021-07": 2315.50, "2021-06": 2290.30, "2021-05": 2260.10,
    "2021-04": 2235.90, "2021-03": 2215.70, "2021-02": 2195.60, "2021-01": 2180.45,
    # 2020
    "2020-12": 2150.60, "2020-11": 2120.40, "2020-10": 2095.10, "2020-09": 2070.60,
    "2020-08": 2050.45, "2020-07": 2030.20, "2020-06": 2015.40, "2020-05": 1995.30,
    "2020-04": 1980.10, "2020-03": 1970.55, "2020-02": 1960.11, "2020-01": 1950.20,
}

conn = get_conn("vulcano")
cur = conn.cursor()

for comp, val in HISTORICO_BASE.items():
    ano, mes = map(int, comp.split("-"))
    last_day = calendar.monthrange(ano, mes)[1]
    data_db = f"{ano}-{mes:02d}-{last_day}"
    
    cur.execute("SELECT MES FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND MES = ?", (data_db,))
    existia = cur.fetchone()
    if existia:
        cur.execute("UPDATE INDICE_REAJUSTE_TABELA SET PERCENTUAL_VARIACAO = ?, VALOR = ? WHERE ID_INDICE_REAJUSTE = 1 AND MES = ?", (val, val, data_db))
    else:
        cur.execute("INSERT INTO INDICE_REAJUSTE_TABELA (ID_INDICE_REAJUSTE, MES, VALOR, PERCENTUAL_VARIACAO) VALUES (1, ?, ?, ?)", (data_db, val, val))
conn.commit()
conn.close()
print("Historical CUB Injected!!!")
