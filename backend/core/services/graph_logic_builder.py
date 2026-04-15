from pydantic import BaseModel
import traceback
from datetime import datetime
from collections import defaultdict
from fastapi import HTTPException
import calendar

class AccountingGraphPipeline:
    @staticmethod
    def api_contabilizacoes(ano: int, mes: int, empresa_id: int = 959, empreendimento_id: str = None):
        from main import get_conn
        from core.services.revenue_time_pipeline import RevenueTimePipeline
        get_receitas_caixa = RevenueTimePipeline.get_receitas_caixa

        conn_vulcano = get_conn("vulcano")
        conn_questor = get_conn("questor")
        
        try:
            cur_v = conn_vulcano.cursor()
            cur_q = conn_questor.cursor()
            
            # Mapeamento do Historico Padrao do Questor
            cur_q.execute("SELECT CODIGOHISTCTB, DESCRHISTCTB FROM HISTORICOCTB")
            hist_questor = {int(r[0]): str(r[1] or "").strip() for r in cur_q.fetchall() if r[0]}
    
            # 1. Obter Empreendimentos Ativos
            query = "SELECT ID, NOME, CODIGOCENTROCUSTO, CONTACUSTO, CONTACLI, CONTAADICLI, CONTACAIXA, CONTAESTAND, CONTAESTCON, OBRACONCLUIDA, CONTAREC, CODIGOHISTVENDA, CODIGOHISTRECEBIMENTO, CODIGOHISTVARIACAO, CODIGOHISTADIANTAMENTO, CODIGOHISTBAIXAADI, CODIGOHISTAPRCUSTO, CODIGOHISTDESPESA, CONTAVARIACAO FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ? AND ATIVO = 'S'"
            params = [empresa_id]
            if empreendimento_id:
                query += f" AND ID = {int(empreendimento_id)}"
                
            cur_v.execute(query, tuple(params))
            empreendimentos = []
            for r in cur_v.fetchall():
                cc = int(r[2]) if r[2] else None
                if cc:
                    empreendimentos.append({
                        "id": r[0], "nome": r[1], "cc": cc,
                        "conta_custo": r[3], "conta_cli": r[4], "conta_adicli": r[5], "conta_caixa": r[6],
                        "conta_estand": r[7], "conta_estcon": r[8], "obra_concluida": r[9], "conta_rec": r[10],
                        "hist_venda": hist_questor.get(r[11] if r[11] else 0, "VENDA UNID"),
                        "hist_rec": hist_questor.get(r[12] if r[12] else 0, "RECEBIMENTO PARCELA UNID"),
                        "hist_var": hist_questor.get(r[13] if r[13] else 0, "VARIACAO UNID"),
                        "hist_adi": hist_questor.get(r[14] if r[14] else 0, "ADIANTAMENTO UNID"),
                        "hist_baixa_adi": hist_questor.get(r[15] if r[15] else 0, "BAIXA ADIANTAMENTO UNID"),
                        "hist_custo": hist_questor.get(r[16] if r[16] else 0, "CUSTO UNID"),
                        "conta_variacao": int(r[18]) if r[18] else 0,  # CONTAVARIACAO para acrescimos
                    })
    
            # Caching Global Vulcano (Receitas e Tributos)
            # PERF: os 2 get_receitas_caixa (mês atual + PQ) rodam em paralelo
            # via ThreadPoolExecutor — reduz o tempo desta etapa à metade.
            try:
                from concurrent.futures import ThreadPoolExecutor

                y, m = int(ano), int(mes)
                if m in (1, 2, 3): pq_y, pq_m = y - 1, 12
                elif m in (4, 5, 6): pq_y, pq_m = y, 3
                elif m in (7, 8, 9): pq_y, pq_m = y, 6
                else: pq_y, pq_m = y, 9

                with ThreadPoolExecutor(max_workers=2) as _pool:
                    _f_atual = _pool.submit(
                        get_receitas_caixa,
                        empresa_id=empresa_id,
                        data_ini=f"{ano}-{str(mes).zfill(2)}",
                        data_fim=f"{ano}-{str(mes).zfill(2)}",
                    )
                    _f_pq = _pool.submit(
                        get_receitas_caixa,
                        empresa_id=empresa_id,
                        data_ini=f"{pq_y}-{str(pq_m).zfill(2)}",
                        data_fim=f"{pq_y}-{str(pq_m).zfill(2)}",
                    )
                    json_resp = _f_atual.result()
                    json_pq   = _f_pq.result()

                receitas_meta    = json_resp.get("dashboard_meta", {})
                impostos_config  = json_resp.get("impostos_config", [])
                receitas_meta_pq = json_pq.get("dashboard_meta", {})

            except Exception as e:
                print(f"Erro ao obter receitas: {e}")
                receitas_meta = {}
                receitas_meta_pq = {}
                impostos_config = []
            
            # Datas de corte
            data_inicio_mes_atual = f"{ano}-{str(mes).zfill(2)}-01"
            if int(mes) == 12:
                data_fim_mes_atual = f"{ano+1}-01-01"
            else:
                data_fim_mes_atual = f"{ano}-{str(int(mes)+1).zfill(2)}-01"
            
            # Auxiliar: Plano Espec
            cur_q.execute("SELECT CONTACTB, CLASSIFCONTA, DESCRCONTA FROM PLANOESPEC WHERE CODIGOEMPRESA = ?", (empresa_id,))
            plano = {r[0]: {"classif": str(r[1]).strip() if r[1] and str(r[1]).strip() else "9.99.99", "nome": r[2]} for r in cur_q.fetchall()}
            
            # Auxiliar: Identificar contas de Imposto a Recolher para considerar apenas Apropriações (Créditos) no físico
            cur_v.execute("SELECT CONTA_CRED_IMP_REC_DARF FROM IMPOSTO")
            contas_imposto_recolher = {str(r[0]).strip() for r in cur_v.fetchall() if r[0]}
                
            contas_fisicas_empresa = {}
            saldo_anterior_por_conta = {} 
    
            # --- SALDO ANTERIOR GLOBAL (Empresa-wide) ---
            cur_q.execute("""
                SELECT 
                    C.CONTACTBDEB, 
                    C.CONTACTBCRED, 
                    G.NATURLCTOCTB, 
                    SUM(G.VALORLCTOGER) as TOTAL
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                WHERE G.CODIGOEMPRESA = ? AND C.DATALCTOCTB < CAST(? AS DATE)
                AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                GROUP BY 1, 2, 3
            """, (empresa_id, data_inicio_mes_atual))
            
            for (c_deb, c_cred, nat, val) in cur_q.fetchall():
                v = float(val or 0)
                if nat == 1 and c_deb:
                    c_deb_str = str(c_deb).strip()
                    if c_deb_str not in contas_imposto_recolher:
                        saldo_anterior_por_conta[c_deb] = saldo_anterior_por_conta.get(c_deb, 0.0) + v
                elif nat == -1 and c_cred:
                    saldo_anterior_por_conta[c_cred] = saldo_anterior_por_conta.get(c_cred, 0.0) - v

            # Helper para identificar contas de resultado (4.x, 5.x etc.)
            # Usado pelo bloco de movimento (ZZ de dezembro) — NÃO afeta saldo_anterior.
            # O saldo_anterior das contas de resultado acumula SEM ZZ, mostrando o
            # histórico completo do projeto (acumulado multiexercício) para auditoria.
            def _e_conta_resultado(cod):
                cl = plano.get(cod, {}).get("classif", "") or ""
                return cl and not cl.startswith(("1.", "2.", "3."))

            cur_q.execute("""
                SELECT 
                    C.CHAVELCTOCTB, C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), G.NATURLCTOCTB, G.VALORLCTOGER, C.CHAVEORIGEM, H.DESCRHISTCTB
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
                WHERE G.CODIGOEMPRESA = ? 
                AND C.DATALCTOCTB >= CAST(? AS DATE) AND C.DATALCTOCTB < CAST(? AS DATE)
                AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                ORDER BY C.DATALCTOCTB ASC
            """, (empresa_id, data_inicio_mes_atual, data_fim_mes_atual))
            
            for (chave, dt, cdeb, ccred, hist_val, nat, val, chave_origem, descr_hist) in cur_q.fetchall():
                if isinstance(hist_val, (bytes, bytearray)):
                    compl = hist_val.decode('cp1252', 'ignore')
                else:
                    compl = str(hist_val) if hist_val else ""
                    
                descr = str(descr_hist or "").strip()
                hist = f"{descr} {compl}".strip()
                    
                v = float(val or 0)
                conta = cdeb if nat == 1 else ccred
                if not conta: continue
                
                conta_str = str(conta).strip()
                if nat == 1 and conta_str in contas_imposto_recolher:
                    continue
                
                if conta not in contas_fisicas_empresa:
                    _classif = plano.get(conta, {}).get("classif", "")
                    _nome = plano.get(conta, {}).get("nome", "Desconhecida")
                    contas_fisicas_empresa[conta] = {
                        "conta": conta,
                        "nome": f"{_classif} - {_nome}" if _classif else _nome,
                        "classif": _classif,
                        "saldo_anterior": saldo_anterior_por_conta.get(conta, 0.0),
                        "movimento_debito": 0.0,
                        "movimento_credito": 0.0,
                        "movimento_liquido": 0.0,
                        "saldo_final": 0.0,
                        "detalhes": []
                    }
                    saldo_anterior_por_conta.pop(conta, None)
                    
                if nat == 1:
                    contas_fisicas_empresa[conta]["movimento_debito"] += v
                    contas_fisicas_empresa[conta]["movimento_liquido"] += v
                else:
                    contas_fisicas_empresa[conta]["movimento_credito"] += v
                    contas_fisicas_empresa[conta]["movimento_liquido"] -= v
                    
                contas_fisicas_empresa[conta]["detalhes"].append({
                    "chave": chave,
                    "data": dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt),
                    "historico": hist,
                    "natureza": "D" if nat == 1 else "C",
                    "valor": v,
                    "origem": "QUESTOR_MANUAL" if not chave_origem else str(chave_origem).strip()
                })
    
            for conta_id, saldo in saldo_anterior_por_conta.items():
                if abs(saldo) > 0.01 and conta_id not in contas_fisicas_empresa:
                    _classif = plano.get(conta_id, {}).get("classif", "")
                    _nome = plano.get(conta_id, {}).get("nome", "Desconhecida")
                    contas_fisicas_empresa[conta_id] = {
                        "conta": conta_id,
                        "nome": f"{_classif} - {_nome}" if _classif else _nome,
                        "classif": _classif,
                        "saldo_anterior": saldo,
                        "movimento_debito": 0.0,
                        "movimento_credito": 0.0,
                        "movimento_liquido": 0.0,
                        "saldo_final": 0.0,
                        "detalhes": []
                    }

            # --- MOVIMENTO DO MÊS: incorpora ARE/ZZ para contas de RESULTADO ---
            # Relevante especialmente em Dezembro: o lançamento ZZ representa o encerramento
            # do exercício e deve aparecer no movimento para auditoria completa.
            cur_q.execute("""
                SELECT 
                    C.CHAVELCTOCTB, C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED,
                    CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), G.NATURLCTOCTB, G.VALORLCTOGER,
                    C.CHAVEORIGEM, H.DESCRHISTCTB
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
                WHERE G.CODIGOEMPRESA = ? 
                AND C.DATALCTOCTB >= CAST(? AS DATE) AND C.DATALCTOCTB < CAST(? AS DATE)
                AND C.CODIGOORIGLCTOCTB = 'ZZ'
                AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                ORDER BY C.DATALCTOCTB ASC
            """, (empresa_id, data_inicio_mes_atual, data_fim_mes_atual))
            for (chave, dt, cdeb, ccred, hist_val, nat, val, chave_origem, descr_hist) in cur_q.fetchall():
                v = float(val or 0)
                conta = cdeb if nat == 1 else ccred
                if not conta: continue
                if not _e_conta_resultado(conta): continue  # Só processa contas de resultado
                conta_str = str(conta).strip()
                if nat == 1 and conta_str in contas_imposto_recolher: continue
                if isinstance(hist_val, (bytes, bytearray)):
                    compl_zz = hist_val.decode('cp1252', 'ignore')
                else:
                    compl_zz = str(hist_val) if hist_val else ""
                descr_zz = str(descr_hist or "").strip()
                hist_zz = f"{descr_zz} {compl_zz}".strip() or "APURAÇÃO RESULTADO EXERCÍCIO (ARE)"
                if conta not in contas_fisicas_empresa:
                    _classif = plano.get(conta, {}).get("classif", "")
                    _nome = plano.get(conta, {}).get("nome", "Desconhecida")
                    contas_fisicas_empresa[conta] = {
                        "conta": conta,
                        "nome": f"{_classif} - {_nome}" if _classif else _nome,
                        "classif": _classif,
                        "saldo_anterior": saldo_anterior_por_conta.pop(conta, 0.0),
                        "movimento_debito": 0.0, "movimento_credito": 0.0,
                        "movimento_liquido": 0.0, "saldo_final": 0.0, "detalhes": []
                    }
                if nat == 1:
                    contas_fisicas_empresa[conta]["movimento_debito"] += v
                    contas_fisicas_empresa[conta]["movimento_liquido"] += v
                else:
                    contas_fisicas_empresa[conta]["movimento_credito"] += v
                    contas_fisicas_empresa[conta]["movimento_liquido"] -= v
                contas_fisicas_empresa[conta]["detalhes"].append({
                    "chave": chave,
                    "data": dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt),
                    "historico": hist_zz,
                    "natureza": "D" if nat == 1 else "C",
                    "valor": v,
                    "origem": "ZZ_ARE"  # marcador para distinguir na Auditoria
                })

            total_anterior_fisico = 0.0
            total_movimento_fisico = 0.0
            total_final_fisico = 0.0
                
            for c, data in contas_fisicas_empresa.items():
                data["saldo_final"] = data["saldo_anterior"] + data["movimento_liquido"]
                total_anterior_fisico += data["saldo_anterior"]
                total_movimento_fisico += data["movimento_liquido"]
                total_final_fisico += data["saldo_final"]
    
            # --- BUSCA DO VULCANO LEGADO (LANCAMENTO_CONTABIL) ---
            contas_legado_empresa = {}
            try:
                cur_v.execute("""
                    SELECT DATA, ID_CONTA_DEBITO, ID_CONTA_CREDITO, HISTORICO, VALOR, CHAVE_ORIGEM, ID_EMPREENDIMENTO
                    FROM LANCAMENTO_CONTABIL
                    WHERE DATA >= CAST(? AS DATE) AND DATA < CAST(? AS DATE)
                """, (data_inicio_mes_atual, data_fim_mes_atual))
                for (dt, cdeb, ccred, hist, val, chave_origem, id_emp) in cur_v.fetchall():
                    v = float(val or 0)
                    if v <= 0.01: continue
                    # Helper local
                    def add_legado(cid, natura):
                        cid = int(cid)
                        if cid not in contas_legado_empresa:
                            _classif = plano.get(cid, {}).get("classif", "")
                            _nm = plano.get(cid, {}).get("nome", "Desconhecida")
                            contas_legado_empresa[cid] = {
                                "conta": cid, "nome": f"{_classif} - {_nm}" if _classif else _nm, "classif": _classif,
                                "saldo_anterior": 0.0, "movimento_debito": 0.0, "movimento_credito": 0.0,
                                "movimento_liquido": 0.0, "saldo_final": 0.0, "detalhes": []
                            }
                        if natura == 'D':
                            contas_legado_empresa[cid]["movimento_debito"] += v
                            contas_legado_empresa[cid]["movimento_liquido"] += v
                        else:
                            contas_legado_empresa[cid]["movimento_credito"] += v
                            contas_legado_empresa[cid]["movimento_liquido"] -= v
                            
                        contas_legado_empresa[cid]["detalhes"].append({
                            "chave": str(chave_origem) if chave_origem else "", "data": dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt),
                            "historico": str(hist) if hist else "", "natureza": natura,
                            "valor": v, "origem": "VU"
                        })
                    if cdeb: add_legado(cdeb, 'D')
                    if ccred: add_legado(ccred, 'C')
            except Exception as e_legado:
                print(f"Aviso: Erro ao ler LANCAMENTO_CONTABIL: {e_legado}")
    
            if not empreendimentos:
                empreendimentos = [{"cc": empreendimento_id or "GERAL", "vendas": []}]

            resultados = []
            for emp in empreendimentos:
                cc = emp["cc"]
                
                # --- INJEÇÃO VIRTUAL EXTRACONTÁBIL (VULCANO) ---
                contas_virtuais = {}
                def inject_virtual_entry(conta_id, valor, natureza, historico, logica="", saldo_ant=0.0):
                    v_float = float(valor or 0)
                    s_ant = float(saldo_ant or 0)
                    if not conta_id: return
                    if abs(v_float) <= 0.01 and abs(s_ant) <= 0.01: return
                    
                    conta_id = int(conta_id)
                    if conta_id not in contas_virtuais:
                        _classif = plano.get(conta_id, {}).get("classif", "")
                        _nome = plano.get(conta_id, {}).get("nome", "Desconhecida")
                        _is_caixa = bool(conta_id == int(emp.get("conta_caixa") or 99999))
                        contas_virtuais[conta_id] = {
                            "conta": conta_id,
                            "nome": f"{_classif} - {_nome}" if _classif else _nome,
                            "classif": _classif,
                            "is_caixa": _is_caixa,
                            "saldo_anterior": 0.0,
                            "movimento_debito": 0.0,
                            "movimento_credito": 0.0,
                            "movimento_liquido": 0.0,
                            "saldo_final": 0.0,
                            "detalhes": []
                        }
                    
                    contas_virtuais[conta_id]["saldo_anterior"] += s_ant
    
                    if abs(v_float) > 0.01:
                        mov = v_float if natureza == 'D' else -v_float
                        if natureza == 'D':
                            contas_virtuais[conta_id]["movimento_debito"] += v_float
                        else:
                            contas_virtuais[conta_id]["movimento_credito"] += v_float
                            
                        contas_virtuais[conta_id]["movimento_liquido"] += mov
                        
                        last_day = calendar.monthrange(int(ano), int(mes))[1]
                        contas_virtuais[conta_id]["detalhes"].append({
                            "chave": "VULCANO_SIM",
                            "data": f"{last_day:02d}/{int(mes):02d}/{ano} (Sim)",
                            "historico": historico,
                            "natureza": natureza,
                            "valor": v_float,
                            "virtual": True,
                            "logica": logica
                        })

    
                # Força a criação das contas parametrizadas para a Auditoria ERP enxergá-las mesmo sem movimento
                for c_key in ["conta_custo", "conta_cli", "conta_adicli", "conta_estand", "conta_estcon", "conta_rec", "conta_variacao"]:
                    cid_raw = emp.get(c_key)
                    if cid_raw and str(cid_raw).strip() and str(cid_raw).strip() != '99999':
                        try:
                            cid = int(cid_raw)
                            # Apenas cria o dict vazio se não existir
                            if cid not in contas_virtuais:
                                _classif = plano.get(cid, {}).get("classif", "")
                                _nome = plano.get(cid, {}).get("nome", "Desconhecida")
                                contas_virtuais[cid] = {
                                    "conta": cid,
                                    "nome": f"{_classif} - {_nome}" if _classif else _nome,
                                    "classif": _classif,
                                    "saldo_anterior": 0.0,
                                    "movimento_debito": 0.0,
                                    "movimento_credito": 0.0,
                                    "movimento_liquido": 0.0,
                                    "saldo_final": 0.0,
                                    "detalhes": []
                                }
                        except ValueError:
                            pass
    
    
                nome_emp = emp["nome"]
                
                # 1. OBTER CUSTO GASTO GLOBAL NA CONTABILIDADE FÍSICA (QUESTOR)
                # PERF: 2 queries idênticas (datas diferentes) unificadas em 1 CASE WHEN
                # → corta N×2 round-trips para N×1 por empreendimento.
                cur_q.execute("""
                    SELECT
                        SUM(CASE WHEN C.DATALCTOCTB < CAST(? AS DATE)
                                 THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_anterior,
                        SUM(CASE WHEN C.DATALCTOCTB < CAST(? AS DATE)
                                 THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_vigente
                    FROM LCTOGER G
                    JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                    WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ?
                    AND C.DATALCTOCTB < CAST(? AS DATE)
                    AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                    AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                """, (
                    data_inicio_mes_atual,  # CASE anterior
                    data_fim_mes_atual,     # CASE vigente
                    empresa_id, emp["cc"],
                    data_fim_mes_atual,     # WHERE cap (o maior dos dois)
                ))
                _row_custo = cur_q.fetchone()
                custo_gasto_anterior = float(_row_custo[0] or 0.0)
                custo_gasto_vigente  = float(_row_custo[1] or 0.0)
    
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
                    
                    # ── COMPOSIÇÃO DO ESTOQUE (INJEÇÃO DE GASTOS FÍSICOS) ──
                    # Usamos os laçamentos mapeados da tela de "Custos" para formar a
                    # perna de Débito do Estoque, refletindo o Ativo construído (Incorrido).
                    # A baixa (Crédito) ocorrerá no split unitário mais abaixo.
                    mov_gasto = custo_gasto_vigente - custo_gasto_anterior
                    if abs(mov_gasto) > 0.01 or abs(custo_gasto_anterior) > 0.01:
                        nat_gasto = 'D' if mov_gasto >= 0 else 'C'
                        logica_gasto = f"Aporte Global Custo Físico Mapeado. Atual: {custo_gasto_vigente:,.2f} - Ant: {custo_gasto_anterior:,.2f}"
                        inject_virtual_entry(c_estoque, abs(mov_gasto), nat_gasto, f"Gastos Incorridos {nome_emp} (CC {emp['cc']})", logica=logica_gasto, saldo_ant=custo_gasto_anterior)
                    
                    c_caixa_banco = emp.get("conta_caixa") or 99999
                    c_cli = emp.get("conta_cli") or 99999
                    c_adi = emp.get("conta_adicli") or 99999
                    c_rec = emp.get("conta_rec") or 99999
                    c_variacao = emp.get("conta_variacao") or 0  # CONTAVARIACAO: conta de variação monetária
                    
                    # Identifica se é lucro presumido com RET
                    ret_global = meta_emp.get("ret", 0)
                    pis_cofins_global = meta_emp.get("pis", 0) + meta_emp.get("cofins", 0)
                    isRet = ret_global > 0 and pis_cofins_global == 0
                    valid_confs = [c for c in impostos_config if c.get("RET") == ("S" if isRet else "N")]
                    
                    try:
                        cur_v.execute("""
                            SELECT V.DESCUNIDIMOB, U.ID, U.METRAGEM 
                            FROM VENDA V
                            JOIN VENDAUNIDADE VU ON VU.IDVENDA = V.ID
                            JOIN UNIDADE U ON U.ID = VU.IDUNIDADE
                            JOIN BLOCO B ON B.ID = U.IDBLOCO
                            WHERE B.IDEMPREENDIMENTO = ?
                        """, (emp["id"],))
                        area_unidades = {}
                        seen_uids_per_desc = {}
                        for r_desc, u_id, r_met in cur_v.fetchall():
                            if r_desc:
                                k = str(r_desc).strip()
                                if k not in area_unidades:
                                    area_unidades[k] = 0.0
                                    seen_uids_per_desc[k] = set()
                                if u_id not in seen_uids_per_desc[k]:
                                    area_unidades[k] += float(r_met or 0.0)
                                    seen_uids_per_desc[k].add(u_id)
                        
                        cur_v.execute("SELECT SUM(U.METRAGEM) FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = ?", (emp["id"],))
                        area_row = cur_v.fetchone()
                        total_area_emp = float(area_row[0]) if area_row and area_row[0] else 1.0
                    except Exception as eval_e:
                        print("Erro lendo metragem das unidades:", eval_e)
                        area_unidades = {}
                        total_area_emp = 1.0
    
                    for uni_data in unidades:
                        uni_nome = uni_data["unidade"]
                        vgv_uni = uni_data["vgv"]
                        if vgv_uni <= 0: continue
    
                        # --- IFRS 15: Detectar se a venda ocorreu NO mês-alvo ---
                        # Se a DATA_VENDA cai no mesmo mês que estamos processando, a unidade
                        # não existia como "vendida" no mês anterior — rec_ant e custo_ant devem ser 0.
                        target_ym = f"{str(ano).zfill(4)}-{str(mes).zfill(2)}"
                        data_venda_str = uni_data.get("data_venda") or ""
                        venda_ym = data_venda_str[:7] if data_venda_str and len(data_venda_str) >= 7 else ""
                        is_nova_venda_mes_alvo = bool(venda_ym) and (venda_ym == target_ym)
    
                        # CUSTO ECONÔMICO (Fração Física / Metragem)
                        # O Custo já reflete a evolução física (foi gasto e medido). Deve-se aplicar apenas o Índice Comercial da unidade.
                        area_da_unidade = area_unidades.get(str(uni_nome).strip(), 0.0)
                        fracao_fisica = (area_da_unidade / total_area_emp) if total_area_emp > 0 else 0.0
                        
                        custo_u_atual = custo_gasto_vigente * fracao_fisica
                        
                        # Se nova venda no mês: custo anterior = 0 (unidade ainda não estava vendida)
                        custo_u_ant = 0.0 if is_nova_venda_mes_alvo else \
                                      custo_gasto_anterior * fracao_fisica
                        mov_custo_u = custo_u_atual - custo_u_ant
                        
                        if abs(mov_custo_u) > 0.01 or abs(custo_u_ant) > 0.01:
                             logica_custo = f"Unid {uni_nome}: Custo Acum CC ({custo_gasto_vigente:,.2f}) * Fração Área ({fracao_fisica*100:.2f}%) = {custo_u_atual:,.2f} - Ant [{custo_u_ant:,.2f}]{'  [NOVA VENDA MÊS]' if is_nova_venda_mes_alvo else ''}"
                             inject_virtual_entry(c_custo, mov_custo_u, 'D', f"{emp.get('hist_aprcusto', 'Apropriação Custo')} UNID {uni_nome}", logica=logica_custo, saldo_ant=custo_u_ant)
                             inject_virtual_entry(c_estoque, mov_custo_u, 'C', f"BAIXA ESTOQUE UNID {uni_nome}", logica=logica_custo, saldo_ant=-custo_u_ant)
    
                        # ── RECEBIMENTOS: Split Principal vs Variação Monetária ─────────────────────────
                        caixa_acum = uni_data["caixa_acumulado"]
                        caixa_mes = uni_data.get("caixa_mes", 0.0)
                        caixa_ant = caixa_acum - caixa_mes
                        
                        if abs(caixa_mes) > 0.01:
                             logica_caixa = f"Unid {uni_nome}: Integralização de Caixa/Banco no mês = {caixa_mes:,.2f}"
                             inject_virtual_entry(c_caixa_banco, abs(caixa_mes), 'D' if caixa_mes > 0 else 'C', f"Recebimento Caixa - Unid {uni_nome}", logica=logica_caixa, saldo_ant=0.0)

                        rec_auferida_atual = vgv_uni * (poc_acumulado_vigente / 100.0)
                        rec_auferida_ant = 0.0 if is_nova_venda_mes_alvo else \
                                          vgv_uni * (poc_acumulado_anterior / 100.0)
                        
                        # -----------------
                        # RECEITA DRE (Econômico)
                        mov_receita_auferida = rec_auferida_atual - rec_auferida_ant
                        logica_rec = f"Unid {uni_nome}: VGV ({vgv_uni:,.2f}) * POC ({poc_acumulado_vigente}%) = {rec_auferida_atual:,.2f} - Ant [{rec_auferida_ant:,.2f}]{'  [NOVA VENDA MÊS — rec_ant forçado 0]' if is_nova_venda_mes_alvo else ''}"
                        if abs(mov_receita_auferida) > 0.01 or abs(rec_auferida_ant) > 0.01:
                             nat_rec = 'C' if mov_receita_auferida > 0 else 'D'
                             nat_cli_rec = 'D' if mov_receita_auferida > 0 else 'C'
                             inject_virtual_entry(c_rec, abs(mov_receita_auferida), nat_rec, f"{emp.get('hist_venda', 'Receita POC')} UNID {uni_nome}", logica=logica_rec, saldo_ant=-rec_auferida_ant)
                             inject_virtual_entry(c_cli, abs(mov_receita_auferida), nat_cli_rec, f"{emp.get('hist_venda', 'Faturamento')} UNID {uni_nome}", logica=logica_rec, saldo_ant=rec_auferida_ant)
                        # -----------------
                        
                        acrescimo_acum = uni_data.get("acrescimo_acumulado", 0.0)
                        acrescimo_mes  = uni_data.get("acrescimo_mes",  0.0)
                        # Só faz o split quando c_variacao está de fato configurado.
                        # Se não estiver, usa caixa_acum cheio para não criar lacuna de
                        # Débito em Clientes sem a contrapartida de CONTAVARIACAO.
                        variacao_configurada = bool(c_variacao and c_variacao not in (0, 99999))

                        if variacao_configurada:
                            caixa_principal_acum = max(0.0, caixa_acum - acrescimo_acum)
                            caixa_principal_ant  = max(0.0, caixa_ant  - (acrescimo_acum - acrescimo_mes))
                        else:
                            caixa_principal_acum = caixa_acum
                            caixa_principal_ant  = caixa_ant

                        # --- Posição Clientes / Adiantamentos ---
                        cli_atual = min(caixa_principal_acum, rec_auferida_atual)
                        adi_atual = max(0.0, caixa_principal_acum - rec_auferida_atual)

                        cli_ant = min(caixa_principal_ant, rec_auferida_ant)
                        adi_ant = max(0.0, caixa_principal_ant - rec_auferida_ant)

                        mov_cli = cli_atual - cli_ant
                        mov_adi = adi_atual - adi_ant
                        _split_info = f" [Acréscimo excluído: {acrescimo_acum:,.2f}]" if variacao_configurada else ""
                        logica_cli = (f"Unid {uni_nome}: Principal Acum ({caixa_principal_acum:,.2f}) preenche Clientes "
                                      f"até Limite da Receita Reconhecida POC ({rec_auferida_atual:,.2f}). "
                                      f"Excesso vira Adiantamento.{_split_info}")


                        if abs(mov_cli) > 0.01 or abs(cli_ant) > 0.01:
                             nat_cli = 'C' if mov_cli > 0 else 'D'
                             inject_virtual_entry(c_cli, abs(mov_cli), nat_cli, f"{emp.get('hist_rec', 'Baixa Cliente')} UNID {uni_nome}", logica=logica_cli, saldo_ant=-cli_ant)
                        
                        if abs(mov_adi) > 0.01 or abs(adi_ant) > 0.01:
                             nat_adi = 'C' if mov_adi > 0 else 'D'
                             inject_virtual_entry(c_adi, abs(mov_adi), nat_adi, f"{emp.get('hist_adi', 'Reconhecimento Adiantamento')} UNID {uni_nome}", logica=logica_cli, saldo_ant=-adi_ant)
                             
                        # --- Variação Monetária: D Clientes/Adi (par completo) + C CONTAVARIACAO ---
                        # Ambas só são geradas JUNTAS (mesma condição) → garante par na Auditoria.
                        if variacao_configurada and acrescimo_mes > 0.01:
                             logica_var = (f"Unid {uni_nome}: Acréscimo/Variação Monetária recebida no mês "
                                          f"({acrescimo_mes:,.2f}). Débito em Clientes se principal ≤ rec. auferida, "
                                          f"senão Adiantamentos.")
                             conta_deb_var = c_cli if caixa_principal_acum <= rec_auferida_atual + 0.01 else c_adi
                             inject_virtual_entry(c_variacao, acrescimo_mes, 'C',
                                 f"{emp.get('hist_var', 'Variação Monetária')} UNID {uni_nome}",
                                 logica=logica_var, saldo_ant=0.0)
                             inject_virtual_entry(conta_deb_var, acrescimo_mes, 'D',
                                 f"{emp.get('hist_var', 'Variação Monetária')} UNID {uni_nome}",
                                 logica=logica_var, saldo_ant=0.0)
                             
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
                        trib_det_acum = uni_data.get("trib_detalhe_caixa_acumulado", {})
                        
                        for cfg in valid_confs:
                            desc = cfg.get("DESCRICAO", "")
                            cta = cfg.get("CONTA_DEB_IMP_SOBRE_VENDA") or 99999
                            
                            bVal = 0.0
                            bVal_acum = 0.0
                            if desc == 'RET': 
                                bVal = trib_det_mes.get("ret", 0)
                                bVal_acum = trib_det_acum.get("ret", 0)
                            elif 'PIS' in desc: 
                                bVal = trib_det_mes.get("pis", 0)
                                bVal_acum = trib_det_acum.get("pis", 0)
                            elif 'COFINS' in desc: 
                                bVal = trib_det_mes.get("cofins", 0)
                                bVal_acum = trib_det_acum.get("cofins", 0)
                            elif 'CSLL' in desc: 
                                bVal = trib_det_mes.get("csll", 0)
                                bVal_acum = trib_det_acum.get("csll", 0)
                            elif 'IRPJ ADIC' in desc.upper(): 
                                bVal = trib_det_mes.get("irpj_adicional", 0)
                                bVal_acum = trib_det_acum.get("irpj_adicional", 0)
                            elif 'IRPJ' in desc: 
                                bVal = trib_det_mes.get("irpj", 0)
                                bVal_acum = trib_det_acum.get("irpj", 0)
                            
                            is_quarter_end = int(mes) in [3, 6, 9, 12]
                            is_trimestral = 'IRPJ' in desc or 'CSLL' in desc
                            
                            # Variáveis locais garantem que PIS/COFINS mensais não sejam infectados pela apuração trimestral
                            _trib_soc_atual = trib_soc_atual
                            _trib_soc_ant = trib_soc_ant
                            _trib_caixa_atual = trib_caixa_atual
                            _trib_caixa_ant = trib_caixa_ant
                            
                            if is_trimestral:
                                meta_pq = receitas_meta_pq.get(nome_emp, {})
                                uni_data_pq = next((u for u in meta_pq.get("unidades", []) if u["unidade"] == uni_nome), {})
                                saldo_soc_pq = uni_data_pq.get("tributos_soc_acumulado", 0.0)
                                saldo_caixa_pq = uni_data_pq.get("tributos_caixa_acumulado", 0.0)
                                
                                if is_quarter_end:
                                    _trib_soc_ant = saldo_soc_pq
                                    _trib_caixa_ant = saldo_caixa_pq
                                else:
                                    _trib_soc_atual = saldo_soc_pq
                                    _trib_soc_ant = saldo_soc_pq
                                    _trib_caixa_atual = saldo_caixa_pq
                                    _trib_caixa_ant = saldo_caixa_pq
                                    
                            _t_dif_atual = max(0, _trib_soc_atual - _trib_caixa_atual)
                            _t_dif_ant = max(0, _trib_soc_ant - _trib_caixa_ant)
                            _mov_dif = _t_dif_atual - _t_dif_ant
                            
                            _t_ant_atual = max(0, _trib_caixa_atual - _trib_soc_atual)
                            _t_ant_ant = max(0, _trib_caixa_ant - _trib_soc_ant)
                            _mov_ant = _t_ant_atual - _t_ant_ant
                            
                            if is_trimestral and not is_quarter_end:
                                continue  # Trimestre off-cycle pula sem gerar DARF nem Diferido 
                            
                            # Qual peso desse imposto na carga tributária toda da unidade?
                            peso_imp = 0.0
                            if uni_data["tributos_caixa_mes"] > 0:
                                peso_imp = bVal / uni_data["tributos_caixa_mes"]
                            elif uni_data["tributos_caixa_acumulado"] > 0:
                                peso_imp = bVal_acum / uni_data["tributos_caixa_acumulado"]
                            else:
                                peso_imp = 1.0 / len(valid_confs) if valid_confs else 1.0
                                
                            if bVal <= 0 and _mov_dif <= 0 and (_trib_soc_atual - _trib_soc_ant) <= 0: continue
                            
                            logica_imp = f"Unid {uni_nome}: Trib Caixa ({_trib_caixa_atual:,.2f}) vs Trib DRE ({_trib_soc_atual:,.2f}). Peso {desc}: {peso_imp*100:.1f}%"
                            if is_trimestral: logica_imp += f" [APURAÇÃO TRIMESTRAL]"
                            
                            m_dif = _mov_dif * peso_imp
                            m_ant = _mov_ant * peso_imp
                            
                            # 1. Base DARF (Fluxo de Caixa Puro que baseia o passivo físico exigível)
                            if abs(bVal) > 0.01 or (is_trimestral and not is_quarter_end):
                                c_deb = cfg.get("CONTA_DEB_IMP_SOBRE_VENDA") or 99999
                                c_cred = cfg.get("CONTA_CRED_IMP_REC_DARF") or 99999
                                # Para manter a tabela estruturada nos meses vazios do Trimestre 
                                v_base = abs(bVal) if not (is_trimestral and not is_quarter_end) else 0.0
                                nat_d = 'D' if bVal >= 0 else 'C'
                                nat_c = 'C' if bVal >= 0 else 'D'
                                inject_virtual_entry(c_deb, v_base, nat_d, f"Despesa Tributária DRE (Base Faturamento) - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=(_trib_caixa_ant * peso_imp))
                                inject_virtual_entry(c_cred, v_base, nat_c, f"Passivo/DARF Exigível (Faturamento) - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=-(_trib_caixa_ant * peso_imp))
                            
                            # 2. Ajuste Diferido (DRE Avançou > Caixa recebido = Criar Passivo Extra)
                            if abs(m_dif) > 0.01:
                                c_deb = cfg.get("CONTA_DEB_IMP_REC_PASSIVO_SOC") or 99999
                                c_cred = cfg.get("CONTA_CRED_IMP_REC_PASSIVO_SOC") or 99999
                                nat_d = 'D' if m_dif > 0 else 'C'
                                nat_c = 'C' if m_dif > 0 else 'D'
                                inject_virtual_entry(c_deb, abs(m_dif), nat_d, f"Provisão Tributo Diferido - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=(_t_dif_ant * peso_imp))
                                inject_virtual_entry(c_cred, abs(m_dif), nat_c, f"Passivo Tributo Diferido - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=-(_t_dif_ant * peso_imp))
                                
                            # 3. Ajuste Antecipado (Caixa recebido > DRE Avançou = Reduzir Despesa via Ativo)
                            if abs(m_ant) > 0.01:
                                c_deb = cfg.get("CONTA_DEB_IMP_APROP_ATIVO") or 99999 
                                c_cred = cfg.get("CONTA_DEB_IMP_SOBRE_VENDA") or 99999 # <-- Correção vital! Creditar a DESPESA para anular o excesso, preservar o DARF físico!
                                nat_d = 'D' if m_ant > 0 else 'C'
                                nat_c = 'C' if m_ant > 0 else 'D'
                                inject_virtual_entry(c_deb, abs(m_ant), nat_d, f"Tributo Antecipado (Ativo) - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=(_t_ant_ant * peso_imp))
                                inject_virtual_entry(c_cred, abs(m_ant), nat_c, f"Estorno Excesso Despesa Trib - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=-(_t_ant_ant * peso_imp))
                # -----------------------------------------------------------------------
                # IFRS 15 — Vendas do mês-alvo sem recebimentos (não estão em receitas_meta)
                # Regra: se POC >= 100% na data_venda, a receita é integralmente reconhecida.
                # Essas unidades não geram linhas no get_receitas_caixa (LEFT JOIN vazio),
                # por isso precisam ser buscadas diretamente aqui.
                # -----------------------------------------------------------------------
                try:
                    data_ini_mes_ctb = f"{ano}-{str(mes).zfill(2)}-01"
                    data_fim_mes_ctb = f"{ano+1}-01-01" if int(mes) == 12 else f"{ano}-{str(int(mes)+1).zfill(2)}-01"
    
                    _cur_nv = conn_vulcano.cursor()  # cursor dedicado — não sobrescreve cur_v
                    # Busca vendas do mês que pertencem a este empreendimento
                    _cur_nv.execute("""
                        SELECT v.ID, v.DESCUNIDIMOB, v.TOTALVENDA, v.DTOPER
                        FROM VENDA v
                        WHERE v.IDEMPREENDIMENTO = ?
                          AND v.DTOPER >= CAST(? AS DATE)
                          AND v.DTOPER <  CAST(? AS DATE)
                          AND (v.DISTRATO IS NULL OR v.DISTRATO <> 'S')
                    """, (emp["id"], data_ini_mes_ctb, data_fim_mes_ctb))
                    vendas_mes = _cur_nv.fetchall()
                    _cur_nv.close()
                    print(f"[INFO nv_scan] {emp['nome'][:35]} ID={emp['id']} poc={poc_acumulado_vigente} vendas_mes={len(vendas_mes)}")
    
                    # contas com fallback seguro (meta_emp pode estar vazio)
                    _c_cli = emp.get("conta_cli") or 99999
                    _c_rec = emp.get("conta_rec") or 99999
    
                    # Unidades já processadas via receitas_meta (têm recebimentos)
                    unidades_ja_processadas = {u["unidade"] for u in meta_emp.get("unidades", [])}
    
                    for vrow in vendas_mes:
                        vid, vuni_raw, vvgv, vdtoper = vrow
                        vuni = (vuni_raw.decode('win1252', 'ignore').strip() if isinstance(vuni_raw, bytes) else str(vuni_raw or '').strip())
                        vvgv = float(vvgv or 0.0)
                        if vvgv <= 0: continue
                        if vuni in unidades_ja_processadas: continue  # já reconhecida via pipeline normal
    
                        if poc_acumulado_vigente < 100.0:
                            print(f"[INFO nv_scan] {vuni} poc={poc_acumulado_vigente} < 100 → pulando")
                            continue
    
                        # Reconhecimento integral: D Clientes / C Receita = VGV
                        logica_nv = (f"[VENDA NO MÊS SEM RECEBIMENTOS] Unid {vuni}: VGV={vvgv:,.2f} | "
                                     f"POC={poc_acumulado_vigente}% → Reconhecimento integral IFRS 15")
                        inject_virtual_entry(_c_cli, vvgv, 'D',
                                             f"Faturamento Direito s/ Venda - Unid {vuni}",
                                             logica=logica_nv, saldo_ant=0.0)
                        inject_virtual_entry(_c_rec, vvgv, 'C',
                                             f"Receita de Vendas POC 100% - Unid {vuni}",
                                             logica=logica_nv, saldo_ant=0.0)
                        print(f"[INFO nova_venda_sem_recb] {emp['nome'][:35]} | {vuni} | VGV={vvgv:,.0f} | INJETADO")
                except Exception as _e_nv:
                    print(f"Erro ao buscar vendas do mês sem recebimentos: {_e_nv}")
    
                # Fecha saldo_final de todas as contas virtuais APÓS todas as injeções (incluindo novas vendas)
                for c, data in contas_virtuais.items():
                    data["saldo_final"] = data["saldo_anterior"] + data["movimento_liquido"]
    
                eh_primeiro = len(resultados) == 0
    
                if len(contas_fisicas_empresa) > 0 or len(contas_virtuais) > 0:
    
                    resultados.append({
                        "empreendimento_id": emp["id"],
                        "empreendimento_nome": emp["nome"],
                        "total_anterior_fisico": total_anterior_fisico if eh_primeiro else 0.0,
                        "total_movimento_fisico": total_movimento_fisico if eh_primeiro else 0.0,
                        "total_final_fisico": total_final_fisico if eh_primeiro else 0.0,
                        "contas_fisicas": list(contas_fisicas_empresa.values()) if eh_primeiro else [],
                        "contas_legado": list(contas_legado_empresa.values()) if eh_primeiro else [],
                        "contas_virtuais": list(contas_virtuais.values())
                    })
                    
            # --- RECEITAS GERAIS (LOCAÇÕES/ALUGUÉIS) P/ IRPJ e TRIBUTOS PRESUMIDOS ---
            if not empreendimento_id:
                try:
                    data_ini_mes = f"{ano}-{str(mes).zfill(2)}-01"
                    data_fim_mes = f"{ano+1}-01-01" if mes == 12 else f"{ano}-{str(mes+1).zfill(2)}-01"
                    
                    # Trimestre Scope setup
                    is_quarter_end = int(mes) in [3, 6, 9, 12]
                    trim_m = 1 if int(mes) in (1,2,3) else 4 if int(mes) in (4,5,6) else 7 if int(mes) in (7,8,9) else 10
                    data_ini_trim = f"{ano}-{str(trim_m).zfill(2)}-01"
                    
                    cur_q.execute('''
                        SELECT C.CODIGOESTAB, SUM(C.VALORCONTABILIMPOSTO)
                        FROM LCTOFISSAICFOP C
                        JOIN LCTOFISSAI I ON C.CODIGOEMPRESA = I.CODIGOEMPRESA AND C.CODIGOESTAB = I.CODIGOESTAB AND C.CHAVELCTOFISSAI = I.CHAVELCTOFISSAI
                        WHERE C.CODIGOEMPRESA = ?
                        AND C.CODIGOCFOP IN (9000200, 9000201)
                        AND I.DATALCTOFIS >= CAST(? AS DATE)
                        AND I.DATALCTOFIS < CAST(? AS DATE)
                        GROUP BY C.CODIGOESTAB
                    ''', (empresa_id, data_ini_mes, data_fim_mes))
                    loc_mes = {r[0]: float(r[1] or 0.0) for r in cur_q.fetchall()}
                    
                    cur_q.execute('''
                        SELECT C.CODIGOESTAB, SUM(C.VALORCONTABILIMPOSTO)
                        FROM LCTOFISSAICFOP C
                        JOIN LCTOFISSAI I ON C.CODIGOEMPRESA = I.CODIGOEMPRESA AND C.CODIGOESTAB = I.CODIGOESTAB AND C.CHAVELCTOFISSAI = I.CHAVELCTOFISSAI
                        WHERE C.CODIGOEMPRESA = ?
                        AND C.CODIGOCFOP IN (9000200, 9000201)
                        AND I.DATALCTOFIS >= CAST(? AS DATE)
                        AND I.DATALCTOFIS < CAST(? AS DATE)
                        GROUP BY C.CODIGOESTAB
                    ''', (empresa_id, data_ini_trim, data_fim_mes))
                    loc_trim = {r[0]: float(r[1] or 0.0) for r in cur_q.fetchall()}
                    
                    cur_q.execute('''
                        SELECT C.CODIGOESTAB, SUM(C.VALORCONTABILIMPOSTO)
                        FROM LCTOFISSAICFOP C
                        JOIN LCTOFISSAI I ON C.CODIGOEMPRESA = I.CODIGOEMPRESA AND C.CODIGOESTAB = I.CODIGOESTAB AND C.CHAVELCTOFISSAI = I.CHAVELCTOFISSAI
                        WHERE C.CODIGOEMPRESA = ?
                        AND C.CODIGOCFOP IN (9000200, 9000201)
                        AND I.DATALCTOFIS < CAST(? AS DATE)
                        GROUP BY C.CODIGOESTAB
                    ''', (empresa_id, data_ini_mes))
                    loc_ant = {r[0]: float(r[1] or 0.0) for r in cur_q.fetchall()}
    
                    cur_q.execute('''
                        SELECT C.CODIGOESTAB, SUM(C.VALORCONTABILIMPOSTO)
                        FROM LCTOFISSAICFOP C
                        JOIN LCTOFISSAI I ON C.CODIGOEMPRESA = I.CODIGOEMPRESA AND C.CODIGOESTAB = I.CODIGOESTAB AND C.CHAVELCTOFISSAI = I.CHAVELCTOFISSAI
                        WHERE C.CODIGOEMPRESA = ?
                        AND C.CODIGOCFOP IN (9000200, 9000201)
                        AND I.DATALCTOFIS < CAST(? AS DATE)
                        GROUP BY C.CODIGOESTAB
                    ''', (empresa_id, data_ini_trim))
                    loc_ant_trim = {r[0]: float(r[1] or 0.0) for r in cur_q.fetchall()}
    
                    todos_estabs = set(list(loc_mes.keys()) + list(loc_ant.keys()) + list(loc_trim.keys()) + list(loc_ant_trim.keys()))
    
                    if todos_estabs:
                        contas_virtuais_loc = {}
                        
                        def get_cv_loc(cid):
                            cid = int(cid)
                            if cid not in contas_virtuais_loc:
                                contas_virtuais_loc[cid] = {
                                    "conta": cid,
                                    "nome": plano.get(cid, {}).get("nome", "Desconhecida"),
                                    "classif": plano.get(cid, {}).get("classif", ""),
                                    "saldo_anterior": 0.0,
                                    "movimento_debito": 0.0,
                                    "movimento_credito": 0.0,
                                    "movimento_liquido": 0.0,
                                    "saldo_final": 0.0,
                                    "detalhes": []
                                }
                            return contas_virtuais_loc[cid]
    
                        def inject_loc_entry(cid, valor_mes, nat, historico, saldo_ant=0.0, logica_str=""):
                            if not cid or cid == 99999 or (valor_mes < 0.01 and abs(saldo_ant) < 0.01):
                                if cid and cid != 99999:
                                    cv = get_cv_loc(cid)
                                    cv["saldo_anterior"] += float(saldo_ant)
                                return
                            cv = get_cv_loc(cid)
                            cv["saldo_anterior"] += float(saldo_ant)
                            last_day = calendar.monthrange(int(ano), int(mes))[1]
                            cv["detalhes"].append({
                                "chave": "LOC_VIRTUAL", "data": f"{last_day:02d}/{int(mes):02d}/{ano} (Serviços/Locação)", "historico": historico,
                                "natureza": nat, "valor": float(valor_mes), "virtual": True,
                                "logica": logica_str
                            })
                            if nat == 'D':
                                cv["movimento_debito"] += float(valor_mes)
                                cv["movimento_liquido"] += float(valor_mes)
                            else:
                                cv["movimento_credito"] += float(valor_mes)
                                cv["movimento_liquido"] -= float(valor_mes)
    
                        confs = [c for c in impostos_config if c.get("RET") == "N"]
                        
                        for estab in todos_estabs:
                            v_loc = loc_mes.get(estab, 0.0)
                            v_loc_trim = loc_trim.get(estab, 0.0)
                            
                            v_loc_ant = loc_ant.get(estab, 0.0)
                            v_loc_ant_trim = loc_ant_trim.get(estab, 0.0)
                            
                            nome_filial = f"Estab {estab} (SCP/Filial)" if estab > 1 else "Matriz"
                            
                            for cfg in confs:
                                desc = cfg.get("DESCRICAO", "").upper()
                                rate = 0.0
                                is_adic = False
                                
                                if 'PIS' in desc: rate = 0.0065
                                elif 'COFINS' in desc: rate = 0.03
                                elif 'IRPJ ADIC' in desc:
                                    is_adic = True
                                elif 'IRPJ' in desc: rate = 0.32 * 0.15
                                elif 'CSLL' in desc: rate = 0.32 * 0.09
                                
                                is_trimestral = 'IRPJ' in desc or 'CSLL' in desc
                                
                                tax_atual = 0.0
                                tax_ant = 0.0
                                logica = ""
                                
                                # Determine calculation base
                                if is_trimestral:
                                    _v_calc = v_loc_trim if is_quarter_end else 0.0
                                    logica = f"Receita TRIMESTRAL {nome_filial}: R$ {v_loc_trim:,.2f}"
                                    _v_ant_calc = v_loc_ant_trim
                                else:
                                    _v_calc = v_loc
                                    logica = f"Receita MENSA {nome_filial}: R$ {v_loc:,.2f}"
                                    _v_ant_calc = v_loc_ant
                                    
                                if is_adic:
                                    if _v_calc > 0:
                                        # Calcular qb_vendas (Caixa do Trimestre) cruzando as metas
                                        qb_vendas = 0.0
                                        for e_name, e_meta in receitas_meta.items():
                                            for u in e_meta.get("unidades", []):
                                                qb_vendas += u.get("caixa_acumulado", 0.0)
                                                
                                        for e_name, e_meta in receitas_meta_pq.items():
                                            for u in e_meta.get("unidades", []):
                                                qb_vendas -= u.get("caixa_acumulado", 0.0)
                                                
                                        qb_vendas = max(0.0, qb_vendas)
                                        
                                        lucro_presumido_misto = (qb_vendas * 0.08) + (_v_calc * 0.32)
                                        quarter_adicional_global = max(0.0, lucro_presumido_misto - 60000.0) * 0.10
                                        
                                        fracao_locacoes = (_v_calc * 0.32) / lucro_presumido_misto if lucro_presumido_misto > 0 else 0.0
                                        tax_atual = quarter_adicional_global * fracao_locacoes
                                        
                                        logica += f" | Base Mista(Loc: {_v_calc*0.32:,.2f} Ven: {qb_vendas*0.08:,.2f}). Excesso sobre 60k rateado em {fracao_locacoes*100:.1f}%"
                                else:
                                    tax_atual = _v_calc * rate
                                    tax_ant = _v_ant_calc * rate
                                    
                                # Se trimestral, forçar lançamento mesmo se 0 na base mensal para transpor saldo_ant na UI
                                do_entry = tax_atual > 0.01 or abs(tax_ant) > 0.01 or is_trimestral
                                
                                if do_entry:
                                    c_deb = cfg.get("CONTA_DEB_IMP_SOBRE_VENDA") or 99999
                                    c_cred = cfg.get("CONTA_CRED_IMP_REC_DARF") or 99999
                                    inject_loc_entry(c_deb, tax_atual, 'D', f"Locação {nome_filial} - {desc}", saldo_ant=tax_ant, logica_str=logica)
                                    inject_loc_entry(c_cred, tax_atual, 'C', f"Locação {nome_filial} - {desc}", saldo_ant=-tax_ant, logica_str=logica)
                                    
                        # Garante inicialização vazia para exibir a conta se ratear zero no mês
                        for cfg in confs:
                            c_deb = cfg.get("CONTA_DEB_IMP_SOBRE_VENDA") or 99999
                            c_cred = cfg.get("CONTA_CRED_IMP_REC_DARF") or 99999
                            if c_deb != 99999: get_cv_loc(c_deb)
                            if c_cred != 99999: get_cv_loc(c_cred)
                        
                        for c, data in contas_virtuais_loc.items():
                            data["saldo_final"] = data["saldo_anterior"] + data["movimento_liquido"]
    
                        if contas_virtuais_loc:
                            resultados.append({
                                "empreendimento_id": "GLOBAL_LOC",
                                "empreendimento_nome": "Geral - Locações e Serviços",
                                "total_anterior_fisico": 0.0,
                                "total_movimento_fisico": 0.0,
                                "total_final_fisico": 0.0,
                                "contas_fisicas": [],
                                "contas_virtuais": list(contas_virtuais_loc.values())
                            })
                except Exception as e:
                    print("Aviso processando Locações Virtuais:", e)
                
            return {"data": resultados}
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn_vulcano.close()
            conn_questor.close()
    
    # ══════════════════════════════════════════════════════════════════════════════
    # /api/auditoria/diagnostico  — Stack de IA para causa raiz Questor ↔ Vulcano
    # ══════════════════════════════════════════════════════════════════════════════
    class DiagnosticoRow(BaseModel):
        conta_id: int
        competencia: str
        saldo_q: float
        saldo_v: float
        n_lanc_q: int = 0
        n_lanc_v: int = 0
    
    class DiagnosticoInput(BaseModel):
        empresa_id: int
        linhas: list[DiagnosticoRow]
        top_n: int = 20
    