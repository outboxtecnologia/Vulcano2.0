"""Substitui o bloco do endpoint api_sero_maodeobra (linha 1007 até 1405) no main.py."""

NEW_ENDPOINT = r'''@app.get("/api/sero/maodeobra")
def api_sero_maodeobra(empresa_id: int = 959, ano: int = 2025, mes: int = 12, cno: str = None):
    """
    Apuracao SERO/INSS real a partir das tabelas Questor.
    - Folha propria:  CALCULORATEIO (evento 5041) + PERIODOCALCULO (competencia)
    - Folha terceiros: TERCEIROPGTO.VALORORIGEMGPS (tem COMPET direto)
    - Cadastro obra:  OUTRAEMPRESA + OUTRAEMPEMP (INSCRFEDPROPRIET = CNPJ proprietario)
    - Metragem:       EMPREENDIMENTO.METRAGEMTOTAL (Vulcano, match por CNPJ)
    - CUB:            INDICE_REAJUSTE_TABELA (Vulcano) com fallback para historico embutido
    O parametro `cno` aceita o CODIGOOUTEMP (string) para filtrar uma obra especifica.
    """
    CUB_FALLBACK = {
        "2025-12": 3100.00, "2025-11": 3080.00, "2025-10": 3060.00, "2025-09": 3040.00,
        "2025-08": 3020.00, "2025-07": 3000.00, "2025-06": 2985.00, "2025-05": 2970.00,
        "2025-04": 2955.00, "2025-03": 2940.00, "2025-02": 2925.00, "2025-01": 2910.00,
        "2024-12": 2895.00, "2024-11": 2880.00, "2024-10": 2865.00, "2024-09": 2850.00,
        "2024-08": 2835.00, "2024-07": 2820.00, "2024-06": 2805.00, "2024-05": 2790.00,
        "2024-04": 2950.40, "2024-03": 2915.30, "2024-02": 2890.20, "2024-01": 2870.12,
        "2023-12": 2855.10, "2023-11": 2840.90, "2023-10": 2825.80, "2023-09": 2810.70,
        "2023-08": 2795.50, "2023-07": 2780.15, "2023-06": 2765.40, "2023-05": 2745.20,
        "2023-04": 2725.10, "2023-03": 2710.60, "2023-02": 2695.45, "2023-01": 2685.30,
        "2022-12": 2675.10, "2022-11": 2665.90, "2022-10": 2645.80, "2022-09": 2625.60,
        "2022-08": 2605.30, "2022-07": 2585.10, "2022-06": 2560.40, "2022-05": 2530.15,
        "2022-04": 2505.80, "2022-03": 2485.45, "2022-02": 2470.30, "2022-01": 2450.10,
        "2021-12": 2435.40, "2021-11": 2415.20, "2021-10": 2390.10, "2021-09": 2365.80,
        "2021-08": 2340.65, "2021-07": 2315.50, "2021-06": 2290.30, "2021-05": 2260.10,
        "2021-04": 2235.90, "2021-03": 2215.70, "2021-02": 2195.60, "2021-01": 2180.45,
        "2020-12": 2150.60, "2020-11": 2120.40, "2020-10": 2095.10, "2020-09": 2070.60,
    }

    def dec(v):
        if v is None: return ""
        if isinstance(v, bytes): return v.decode("win1252", "ignore").strip()
        return str(v).strip()

    conn_v = get_conn("vulcano")
    conn_q = get_conn("questor")
    try:
        cur_v = conn_v.cursor()
        cur_q = conn_q.cursor()
        compet_alvo = f"{ano}-{str(mes).zfill(2)}"

        # 1. CUB: tenta banco Vulcano, fallback para dicionario embutido
        cub_history = dict(CUB_FALLBACK)
        try:
            cur_v.execute("SELECT MES, VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND VALOR IS NOT NULL ORDER BY MES ASC")
            for r in cur_v.fetchall():
                cub_history[str(r[0])[:7]] = float(r[1])
        except Exception:
            pass
        cub_vigente = cub_history.get(compet_alvo, 2950.0)

        # 2. Metragem por CNPJ do proprietario (Vulcano)
        cur_v.execute("SELECT COUNT(*) FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='EMPREENDIMENTO' AND TRIM(RDB$FIELD_NAME)='CNPJ'")
        tem_cnpj_v = cur_v.fetchone()[0] > 0
        metragem_por_cnpj = {}
        if tem_cnpj_v:
            cur_v.execute("SELECT CNPJ, COALESCE(METRAGEMTOTAL, 0) FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ?", (empresa_id,))
            for r in cur_v.fetchall():
                cnpj_limpo = "".join(filter(str.isdigit, dec(r[0])))
                if cnpj_limpo:
                    metragem_por_cnpj[cnpj_limpo] = float(r[1] or 0)

        # 3. Cadastro de OUTRAEMPRESA + INSCRFEDPROPRIET (Questor)
        outemp_filtro = ""
        params_outemp = [empresa_id]
        if cno:
            try:
                outemp_filtro = " AND OEE.CODIGOOUTEMP = ?"
                params_outemp.append(int(cno))
            except ValueError:
                pass

        cur_q.execute(
            "SELECT OE.CODIGOOUTEMP, OE.NOMEOUTEMP, OE.INSCRFEDERAL, OEE.INSCRFEDPROPRIET"
            " FROM OUTRAEMPEMP OEE"
            " JOIN OUTRAEMPRESA OE ON OE.CODIGOOUTEMP = OEE.CODIGOOUTEMP"
            " WHERE OEE.CODIGOEMPRESA = ?" + outemp_filtro,
            tuple(params_outemp)
        )
        obras_cadastro = {}
        for r in cur_q.fetchall():
            cod = r[0]
            propri_limpo = "".join(filter(str.isdigit, dec(r[3])))
            obras_cadastro[cod] = {
                "nome": dec(r[1]),
                "inscricao": dec(r[2]),
                "cnpj_proprietario": dec(r[3]),
                "metragem": metragem_por_cnpj.get(propri_limpo, 0.0),
            }

        if not obras_cadastro:
            return {
                "resumo": {
                    "mao_de_obra": 0.0, "mao_de_obra_folha": 0.0,
                    "mao_de_obra_terceiros_gps": 0.0,
                    "total_inss": 0.0, "cub_vigente": cub_vigente, "area_total": 0.0
                },
                "alocacoes_terceiros": [],
                "curva_s": [],
                "aviso": "Nenhuma OUTRAEMPRESA vinculada a esta empresa no Questor."
            }

        outemps_list = list(obras_cadastro.keys())
        placeholders = ",".join("?" * len(outemps_list))

        # 4. Folha propria: CALCULORATEIO evento 5041 + PERIODOCALCULO
        cur_q.execute(
            "SELECT C.CODIGOOUTEMP, P.COMPET, SUM(C.VALOREVENTO)"
            " FROM CALCULORATEIO C"
            " JOIN PERIODOCALCULO P ON P.CODIGOPERCALCULO = C.CODIGOPERCALCULO"
            " WHERE C.CODIGOEVENTO = 5041 AND C.CODIGOEMPRESA = ?"
            " AND C.CODIGOOUTEMP IN (" + placeholders + ")"
            " GROUP BY C.CODIGOOUTEMP, P.COMPET ORDER BY P.COMPET",
            tuple([empresa_id] + outemps_list)
        )
        folha_rows = cur_q.fetchall()

        # 5. Terceiros GPS: TERCEIROPGTO.VALORORIGEMGPS (COMPET direto)
        cur_q.execute(
            "SELECT CODIGOOUTEMP, COMPET, SUM(VALORORIGEMGPS)"
            " FROM TERCEIROPGTO"
            " WHERE CODIGOEMPRESA = ? AND CODIGOOUTEMP IN (" + placeholders + ")"
            " GROUP BY CODIGOOUTEMP, COMPET ORDER BY COMPET",
            tuple([empresa_id] + outemps_list)
        )
        terceiro_rows = cur_q.fetchall()

        # 6. Agrega por competencia
        from collections import defaultdict
        historico_mensal = defaultdict(lambda: {"realizado": 0.0, "previsto": 0.0})
        total_folha = total_terceiros = 0.0
        alocacoes_t = []

        for (outemp, compet_dt, valor) in folha_rows:
            comp = str(compet_dt)[:7]
            v = float(valor or 0)
            historico_mensal[comp]["realizado"] += v
            total_folha += v

        for (outemp, compet_dt, valor) in terceiro_rows:
            comp = str(compet_dt)[:7]
            v = float(valor or 0)
            historico_mensal[comp]["realizado"] += v
            total_terceiros += v
            info = obras_cadastro.get(outemp, {})
            alocacoes_t.append({
                "compet": comp, "codigooutemp": outemp,
                "nome_obra": info.get("nome", ""),
                "cno": info.get("inscricao", ""),
                "valor_recolhido": round(v, 2),
            })

        # 7. Projecao CUB (previsto) para curva-S
        area_total = sum(o["metragem"] for o in obras_cadastro.values())
        if area_total > 0 and historico_mensal:
            data_ini = sorted(historico_mensal.keys())[0]
            y0, m0 = map(int, data_ini.split("-"))
            for offset in range(72):
                cm = m0 + offset; cy = y0
                while cm > 12: cm -= 12; cy += 1
                cs = f"{cy}-{str(cm).zfill(2)}"
                if cs > compet_alvo: break
                historico_mensal[cs]["previsto"] += (area_total * cub_history.get(cs, 2950.0) * 0.20) / 48.0

        curva_s = []
        acc_real = acc_prev = 0.0
        for comp in sorted(historico_mensal.keys()):
            if comp > compet_alvo: break
            acc_real += historico_mensal[comp]["realizado"]
            acc_prev += historico_mensal[comp]["previsto"]
            curva_s.append({
                "mes": comp,
                "realizado_mes": round(historico_mensal[comp]["realizado"], 2),
                "previsto_mes":  round(historico_mensal[comp]["previsto"], 2),
                "realizado": round(acc_real, 2),
                "previsto":  round(acc_prev, 2),
            })

        total_mao_de_obra = total_folha + total_terceiros
        diferenca_base = acc_prev - acc_real
        total_inss = max(diferenca_base * 0.368, 0.0)

        return {
            "resumo": {
                "mao_de_obra":               round(total_mao_de_obra, 2),
                "mao_de_obra_folha":         round(total_folha, 2),
                "mao_de_obra_terceiros_gps": round(total_terceiros, 2),
                "total_inss":                round(total_inss, 2),
                "cub_vigente":               cub_vigente,
                "area_total":                round(area_total, 2),
            },
            "alocacoes_terceiros": sorted(alocacoes_t, key=lambda x: x["compet"], reverse=True),
            "curva_s": curva_s,
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn_v.close()
        conn_q.close()

'''

# START=linha 1007 (idx 1006), END=linha antes de @app.get("/api/dimob/preview") = linha 1405 (idx 1404)
START = 1006  # inclusive, base-0
END   = 1405  # exclusive, base-0  (a linha 1406 é @app.get("/api/dimob/preview"))

with open("main.py", "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

print(f"Total de linhas antes: {len(lines)}")
print(f"Linha {START+1}: {lines[START][:80].strip()}")
print(f"Linha {END+1}:   {lines[END][:80].strip()}")

new_lines = lines[:START] + [NEW_ENDPOINT] + lines[END:]

with open("main.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"Total de linhas depois: {len(new_lines)}")
print("main.py atualizado!")
