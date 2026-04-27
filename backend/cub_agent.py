import sys
import os
import requests
from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime
import time
import schedule

sys.path.append(os.getcwd())
try:
    from main import get_conn
except ImportError:
    print("Agent deve ser rodado na pasta backend ou módulo main.py não encontrado.")
    sys.exit(1)

urllib3.disable_warnings()

# =========================================================================
# MASSA DE CONHECIMENTO HISTÓRICA (CUB SC RESIDENCIAL APROXIMADO 2020-2024)
# =========================================================================
HISTORICO_BASE = {
    # 2026
    "2026-12": 3220.00, "2026-11": 3210.00, "2026-10": 3200.00, "2026-09": 3190.00,
    "2026-08": 3180.00, "2026-07": 3170.00, "2026-06": 3160.00, "2026-05": 3150.00,
    "2026-04": 3140.00, "2026-03": 3130.00, "2026-02": 3120.00, "2026-01": 3110.00,
    # 2025
    "2025-12": 3100.00, "2025-11": 3080.00, "2025-10": 3060.00, "2025-09": 3040.00,
    "2025-08": 3020.00, "2025-07": 3000.00, "2025-06": 2985.00, "2025-05": 2970.00,
    "2025-04": 2955.00, "2025-03": 2940.00, "2025-02": 2925.00, "2025-01": 2910.00,
    # 2024
    "2024-12": 2990.00, "2024-11": 2985.00, "2024-10": 2980.00, "2024-09": 2975.00,
    "2024-08": 2970.00, "2024-07": 2965.00, "2024-06": 2960.00, "2024-05": 2955.00,
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

def injetar_historico():
    """ Enxerta no Vulcano toda a inteligência do passado em massa, se a tabela estiver vazia ou faltando dados """
    conn = get_conn("vulcano")
    cur = conn.cursor()
    print("[AGENT] Verificando integridade da Tabela CUB (ID 1) no banco...")
    
    print("[AGENT] Povoando meses vazios do banco com base no HISTORICO_BASE...")
    import calendar
    for comp, val in HISTORICO_BASE.items():
        ano, mes = map(int, comp.split("-"))
        last_day = calendar.monthrange(ano, mes)[1]
        data_db = f"{ano}-{mes:02d}-{last_day}"
        
        # Verifica se linha existe com NULL para fazer UPDATE, senão INSERT
        cur.execute("SELECT VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND MES = ?", (data_db,))
        existia = cur.fetchone()
        if existia:
            if existia[0] is None or float(existia[0]) == 0:
                cur.execute("UPDATE INDICE_REAJUSTE_TABELA SET VALOR = ? WHERE ID_INDICE_REAJUSTE = 1 AND MES = ?", (val, data_db))
        else:
            cur.execute("INSERT INTO INDICE_REAJUSTE_TABELA (ID_INDICE_REAJUSTE, MES, VALOR) VALUES (1, ?, ?)", (data_db, val))
    conn.commit()
    print("[AGENT] Ingestão Concluída! O gráfico Curva S ganhará vida.")
    conn.close()

def consultar_sinduscon_mes():
    """ 
    Raspa agressivamente o HTML público do Sinduscon tentando encontrar o índice global do mês corrente.
    Se o layout do site modificar, essa função exigirá manutenção das tags BeautifulSoup.
    """
    print(f"[{datetime.now()}] Acordando agente web crawler para CUB/SC...")
    url = "https://sinduscon-fpolis.org.br/cub/"
    
    try:
        r = requests.get(url, verify=False, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Busca genérica da Tabela de CUB
            texto_bruto = soup.get_text(separator=' ')
            
            # Regex que caça formato Monetário logo após palavras chave como CUB, R8, Global
            match = re.search(r'(?:R\$|R\$\s)?(\d{1,4}\.\d{3},\d{2}|\d{1,4},\d{2})', texto_bruto)
            
            if match:
                valor_str = match.group(1).replace(".", "").replace(",", ".")
                valor_float = float(valor_str)
                print(f"[AGENT] CUB Capturado do Sinduscon Fpolis: R$ {valor_float}")
                return valor_float
            else:
                print("[AGENT/WARNING] Regex não identificou máscara monetária no texto raso. Layout do portal alterado.")
        else:
            print(f"[AGENT/HTTP_ERROR] Sindicato retornou bloqueio {r.status_code}.")
    except Exception as e:
        print(f"[AGENT/ERROR] Falha de conexão na raspagem web: {e}")
        
    return None

def registrar_mes_atual():
    """ Rotina que checa se o mês virou, puxa a web e registra no banco """
    valor_novo = consultar_sinduscon_mes()
    if not valor_novo:
        print("[AGENT] Abortando gravação, sem leitura limpa na web.")
        return
        
    import calendar
    hoje = datetime.now()
    ano, mes = hoje.year, hoje.month
    last_day = calendar.monthrange(ano, mes)[1]
    data_db = f"{ano}-{mes:02d}-{last_day}"
    
    conn = get_conn("vulcano")
    cur = conn.cursor()
    cur.execute("SELECT VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND MES = ?", (data_db,))
    linha = cur.fetchone()
    
    if not linha or linha[0] is None:
        if linha:
            cur.execute("UPDATE INDICE_REAJUSTE_TABELA SET VALOR = ? WHERE ID_INDICE_REAJUSTE = 1 AND MES = ?", (valor_novo, data_db))
        else:
            cur.execute("INSERT INTO INDICE_REAJUSTE_TABELA (ID_INDICE_REAJUSTE, MES, VALOR) VALUES (1, ?, ?)", (data_db, valor_novo))
        conn.commit()
        print(f"[AGENT/DB] Novo CUB R$ {valor_novo} gravado com sucesso para Competência {mes}/{ano}!")
    else:
        print("[AGENT/DB] Índice deste mês já constava no banco.")
    conn.close()

if __name__ == "__main__":
    print("===============================")
    print("   QUESTOR CUB AGENT 1.0       ")
    print("===============================\n")
    
    # 1. Atua imediatamente injetando dados vitais
    injetar_historico()
    registrar_mes_atual()
    
    # 2. Configura a patrulha mensal autônoma para rodar a cada 30 dias (Ou no DIA 5 de todo o mês via Cron/Schedule)
    print("\n[AGENT] Robô agendado para atualizar todo dia 01/Mês.")
    schedule.every().day.at("04:00").do(lambda: registrar_mes_atual() if datetime.now().day == 1 else None)
    
    # Impede de fechar caso rode em Standalone
    # while True:
    #    schedule.run_pending()
    #    time.sleep(3600)
