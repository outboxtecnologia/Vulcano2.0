from __future__ import annotations

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
            # REGRA: incluir TODOS os empreendimentos que tenham conta de estoque
            # configurada (CONTAESTAND ou CONTAESTCON), independente de ter CC.
            # - COM CC: gastos de obra vem do LCTOGER filtrado pelo CC
            # - SEM CC: gastos de obra vem do LCTOCTB filtrado pela conta de estoque
            # Sem CODIGOHISTDISTRATO: essa coluna nao existe em EMPREENDIMENTO e o SELECT
            # inteiro falhava com "Column unknown", derrubando /api/questor/contabilizacoes
            # (e com ela as telas de Contabilizacoes e Auditoria ERP) com 500.
            # O distrato e tratado por DISTRATOCTB e por VENDA.DISTRATO/DATADISTRATO; aqui
            # so se precisa do rotulo do historico, que cai no default "DISTRATO UNID".
            query = "SELECT ID, NOME, CODIGOCENTROCUSTO, CONTACUSTO, CONTACLI, CONTAADICLI, CONTACAIXA, CONTAESTAND, CONTAESTCON, OBRACONCLUIDA, CONTAREC, CODIGOHISTVENDA, CODIGOHISTRECEBIMENTO, CODIGOHISTVARIACAO, CODIGOHISTADIANTAMENTO, CODIGOHISTBAIXAADI, CODIGOHISTAPRCUSTO, CODIGOHISTDESPESA, CONTAVARIACAO, CODIGO_HIST_ESTORNO_CUSTO FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ? AND ATIVO = 'S'"
            params = [empresa_id]
            if empreendimento_id:
                query += f" AND ID = {int(empreendimento_id)}"
                
            cur_v.execute(query, tuple(params))
            empreendimentos = []
            for r in cur_v.fetchall():
                cc = int(r[2]) if r[2] else None
                conta_estand_raw  = r[7]
                conta_estcon_raw  = r[8]
                ob_conc = str(r[9] or 'N').strip().upper() == 'S'
                # Conta de estoque esperada para este empreendimento
                c_est_raw = conta_estcon_raw if ob_conc else conta_estand_raw
                tem_conta_estoque = bool(c_est_raw and str(c_est_raw).strip())

                # REGRA GERAL: incluir apenas se tiver CC (gastos via LCTOGER)
                # OU se tiver conta de estoque configurada mesmo sem CC.
                # Empreendimentos sem CC e sem conta_estoque nao tem dados contabeis mapeados.
                if not cc and not tem_conta_estoque:
                    continue  # nada a mostrar

                empreendimentos.append({
                    "id": r[0], "nome": r[1], "cc": cc,
                    "conta_custo": r[3], "conta_cli": r[4], "conta_adicli": r[5], "conta_caixa": r[6],
                    "conta_estand": r[7], "conta_estcon": r[8], "obra_concluida": r[9], "conta_rec": r[10],
                    "hist_venda": hist_questor.get(r[11] if r[11] else 0, "VENDA UNID"),
                    "hist_rec": hist_questor.get(r[12] if r[12] else 0, "RECEBIMENTO PARCELA UNID"),
                    "hist_var": hist_questor.get(r[13] if r[13] else 0, "VARIACAO UNID"),
                    "hist_adi": hist_questor.get(r[14] if r[14] else 0, "ADIANTAMENTO UNID"),
                    "hist_baixa_adi": hist_questor.get(r[15] if r[15] else 0, "BAIXA ADIANTAMENTO UNID"),
                    "hist_aprcusto": hist_questor.get(r[16] if r[16] else 0, "CUSTO UNID"),
                    "conta_variacao": int(r[18]) if r[18] else 0,
                    "hist_estorno_custo": hist_questor.get(r[19] if r[19] else 0, "ESTORNO CUSTO UNID"),
                    "hist_distrato": "DISTRATO UNID",  # ver nota na query: nao ha coluna de historico de distrato
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
                    _kwargs = dict(
                        empresa_id=empresa_id,
                        empreendimentos_ids=str(empreendimento_id) if empreendimento_id else None,
                        prune_idle=False
                    )
                    _f_atual = _pool.submit(
                        get_receitas_caixa,
                        data_ini=f"{ano}-{str(mes).zfill(2)}",
                        data_fim=f"{ano}-{str(mes).zfill(2)}",
                        **_kwargs,
                    )
                    _f_pq = _pool.submit(
                        get_receitas_caixa,
                        data_ini=f"{pq_y}-{str(pq_m).zfill(2)}",
                        data_fim=f"{pq_y}-{str(pq_m).zfill(2)}",
                        **_kwargs,
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

            import sqlite3
            memoria_arraste = {}
            try:
                from db_app import connect_app
                conn_poc = connect_app()
                cur_poc = conn_poc.cursor()
                cur_poc.execute('CREATE TABLE IF NOT EXISTS auditoria_memoria_arraste (chave_lancamento TEXT PRIMARY KEY, conta_destino TEXT, origem TEXT, data_modificacao TIMESTAMP)')
                cur_poc.execute('SELECT chave_lancamento, conta_destino FROM auditoria_memoria_arraste')
                for chv, dest in cur_poc.fetchall():
                    memoria_arraste[str(chv).strip()] = str(dest).strip()
                conn_poc.close()
            except Exception as ei:
                print('Erro ao carregar memoria de arraste do sqlite:', ei)


            cur_v.execute("""
                SELECT UPPER(E.NOME), V.DESCUNIDIMOB 
                FROM VENDA V 
                JOIN VENDAUNIDADE VU ON VU.IDVENDA = V.ID 
                JOIN UNIDADE U ON U.ID = VU.IDUNIDADE 
                JOIN BLOCO B ON B.ID = U.IDBLOCO 
                JOIN EMPREENDIMENTO E ON E.ID = B.IDEMPREENDIMENTO
            """)
            import re
            contrato_to_apto = {}
            for e_nome, desc in cur_v.fetchall():
                if desc and e_nome:
                    d_str = str(desc).strip()
                    m_c = re.search(r'^(\d+)\s*/', d_str)
                    m_u = re.search(r'APTO\s*(\d+)', d_str, re.IGNORECASE)
                    if m_c and m_u:
                        emp_words = set(re.findall(r'[A-Z]{4,}', str(e_nome)))
                        for w in emp_words:
                            if w not in ('RESIDENCIAL', 'EDIFICIO', 'CONDOMINIO', 'EMPREENDIMENTO'):
                                if w not in contrato_to_apto: contrato_to_apto[w] = {}
                                contrato_to_apto[w][m_c.group(1)] = m_u.group(1)

            def _append_apto_if_matched(hist_str):
                hist_mod = hist_str
                for emp_word in contrato_to_apto.keys():
                    m = re.search(rf'{emp_word}\s*-?\s*0*(\d{{1,4}})\b', hist_mod, re.IGNORECASE)
                    if m:
                        c_num = m.group(1)
                        if c_num in contrato_to_apto[emp_word]:
                            hist_mod += f" [APTO {contrato_to_apto[emp_word][c_num]}]"
                            break
                return hist_mod


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
                hist = _append_apto_if_matched(hist)
                    
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
                    
                override = memoria_arraste.get(str(chave).strip())
                contrapartida_id = ccred if nat == 1 else cdeb
                copt_nome = plano.get(contrapartida_id, {}).get("nome", "") if contrapartida_id else ""
                contrapartida_str = f"{contrapartida_id} - {copt_nome}" if copt_nome else str(contrapartida_id or "")

                contas_fisicas_empresa[conta]["detalhes"].append({
                    "chave": chave,
                    "data": dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt),
                    "historico": hist,
                    "natureza": "D" if nat == 1 else "C",
                    "valor": v,
                    "origem": "QUESTOR_MANUAL" if not chave_origem else str(chave_origem).strip(),
                    "contrapartida": contrapartida_str,
                    **({"override_apto": override} if override else {})
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
                hist_zz = _append_apto_if_matched(hist_zz)

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
                
                override = memoria_arraste.get(str(chave).strip())
                contrapartida_id = ccred if nat == 1 else cdeb
                copt_nome = plano.get(contrapartida_id, {}).get("nome", "") if contrapartida_id else ""
                contrapartida_str = f"{contrapartida_id} - {copt_nome}" if copt_nome else str(contrapartida_id or "")

                contas_fisicas_empresa[conta]["detalhes"].append({
                    "chave": chave,
                    "data": dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt),
                    "historico": hist_zz,
                    "natureza": "D" if nat == 1 else "C",
                    "valor": v,
                    "origem": "ZZ_ARE" if not chave_origem else str(chave_origem).strip(),
                    "contrapartida": contrapartida_str,
                    **({"override_apto": override} if override else {})
                })

            # ══════════════════════════════════════════════════════════════════
            # PASSAGEM SUPLEMENTAR: Contas de Estoque de Obra (LCTOCTB direto)
            # ══════════════════════════════════════════════════════════════════
            # Contas como CONTAESTAND (ex: 5639 Stuttgart) têm seus lançamentos
            # físicos no LCTOCTB sem correspondente no LCTOGER global (o LCTOGER
            # registra o custo pelo CC, mas não pela conta contábil do ativo).
            # O JOIN interno LCTOGER→LCTOCTB deixa essas contas invisíveis na
            # coluna Questor da Auditoria. Esta passagem resolve isso:
            #   1. Coleta todos os códigos de conta de estoque dos empreendimentos
            #   2. Para cada conta ausente em contas_fisicas_empresa, lê LCTOCTB
            #      diretamente e inclui o saldo anterior e movimento do mês.
            try:
                contas_estoque_ids = set()
                for emp_s in empreendimentos:
                    ob_s = str(emp_s.get("obra_concluida", "N")).strip().upper() == 'S'
                    c_raw = emp_s.get("conta_estcon") if ob_s else emp_s.get("conta_estand")
                    if c_raw:
                        try:
                            contas_estoque_ids.add(int(c_raw))
                        except (ValueError, TypeError):
                            pass

                for cid_est in contas_estoque_ids:
                    if cid_est in contas_fisicas_empresa:
                        continue  # ja coberta pelo LCTOGER — nao duplicar

                    # Saldo anterior direto no LCTOCTB
                    cur_q.execute("""
                        SELECT
                            SUM(CASE WHEN CONTACTBDEB  = ? THEN VALORLCTOCTB ELSE 0 END) AS deb,
                            SUM(CASE WHEN CONTACTBCRED = ? THEN VALORLCTOCTB ELSE 0 END) AS cred
                        FROM LCTOCTB
                        WHERE CODIGOEMPRESA = ?
                          AND DATALCTOCTB < CAST(? AS DATE)
                          AND (CODIGOORIGLCTOCTB IS NULL OR CODIGOORIGLCTOCTB <> 'ZZ')
                    """, (cid_est, cid_est, empresa_id, data_inicio_mes_atual))
                    r_ant = cur_q.fetchone()
                    saldo_ant_est = float(r_ant[0] or 0) - float(r_ant[1] or 0)

                    # Movimento do mês direto no LCTOCTB
                    cur_q.execute("""
                        SELECT CHAVELCTOCTB, DATALCTOCTB, CONTACTBDEB, CONTACTBCRED,
                               CAST(COMPLHIST AS BLOB SUB_TYPE 0), VALORLCTOCTB, CODIGOHISTCTB
                        FROM LCTOCTB
                        WHERE CODIGOEMPRESA = ?
                          AND (CONTACTBDEB = ? OR CONTACTBCRED = ?)
                          AND DATALCTOCTB >= CAST(? AS DATE)
                          AND DATALCTOCTB <  CAST(? AS DATE)
                          AND (CODIGOORIGLCTOCTB IS NULL OR CODIGOORIGLCTOCTB <> 'ZZ')
                        ORDER BY DATALCTOCTB ASC
                    """, (empresa_id, cid_est, cid_est,
                          data_inicio_mes_atual, data_fim_mes_atual))
                    rows_est = cur_q.fetchall()

                    if abs(saldo_ant_est) < 0.01 and not rows_est:
                        continue  # conta realmente vazia — nao criar entrada fantasma

                    _classif_est = plano.get(cid_est, {}).get("classif", "")
                    _nome_est    = plano.get(cid_est, {}).get("nome", "Desconhecida")
                    contas_fisicas_empresa[cid_est] = {
                        "conta": cid_est,
                        "nome": f"{_classif_est} - {_nome_est}" if _classif_est else _nome_est,
                        "classif": _classif_est,
                        "saldo_anterior": saldo_ant_est,
                        "movimento_debito": 0.0,
                        "movimento_credito": 0.0,
                        "movimento_liquido": 0.0,
                        "saldo_final": 0.0,
                        "detalhes": []
                    }

                    for (chave_e, dt_e, cdeb_e, ccred_e, hist_e, val_e, hist_cod) in rows_est:
                        v_e = float(val_e or 0)
                        if v_e < 0.01:
                            continue
                        if isinstance(hist_e, (bytes, bytearray)):
                            compl_e = hist_e.decode('cp1252', 'ignore')
                        else:
                            compl_e = str(hist_e or "")
                        hn = hist_questor.get(hist_cod, "") if hist_cod else ""
                        hist_txt = f"{hn} {compl_e}".strip()

                        if cdeb_e == cid_est:
                            contas_fisicas_empresa[cid_est]["movimento_debito"]  += v_e
                            contas_fisicas_empresa[cid_est]["movimento_liquido"] += v_e
                            nat_str = "D"
                            contrapartida_id = ccred_e
                        else:
                            contas_fisicas_empresa[cid_est]["movimento_credito"] += v_e
                            contas_fisicas_empresa[cid_est]["movimento_liquido"] -= v_e
                            nat_str = "C"
                            contrapartida_id = cdeb_e

                        copt_nome = plano.get(contrapartida_id, {}).get("nome", "") if contrapartida_id else ""
                        contrapartida_str = f"{contrapartida_id} - {copt_nome}" if copt_nome else str(contrapartida_id or "")

                        contas_fisicas_empresa[cid_est]["detalhes"].append({
                            "chave": chave_e,
                            "data":  dt_e.strftime('%d/%m/%Y') if hasattr(dt_e, 'strftime') else str(dt_e),
                            "historico": hist_txt,
                            "natureza": nat_str,
                            "valor": v_e,
                            "origem": "QUESTOR_ESTOQUE_DIRETO",
                            "contrapartida": contrapartida_str
                        })

                    print(f"[FISICO-ESTOQUE] conta={cid_est} | "
                          f"saldo_ant={saldo_ant_est:,.0f} | "
                          f"lancamentos_mes={len(rows_est)}")
            except Exception as _e_est:
                print(f"[AVISO] Passagem suplementar estoque: {_e_est}")

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
                            
                        hist_legado = str(hist).strip() if hist else ""
                        hist_legado = _append_apto_if_matched(hist_legado)

                        str_chv_or = str(chave_origem).strip() if chave_origem else ""
                        override = memoria_arraste.get(str_chv_or)
                        contrapartida_id = ccred if natura == 'D' else cdeb
                        copt_nome = plano.get(contrapartida_id, {}).get("nome", "") if contrapartida_id else ""
                        contrapartida_str = f"{contrapartida_id} - {copt_nome}" if copt_nome else str(contrapartida_id or "")

                        contas_legado_empresa[cid]["detalhes"].append({
                            "chave": str_chv_or, "data": dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt),
                            "historico": hist_legado, "natureza": natura,
                            "valor": v, "origem": "VU",
                            "contrapartida": contrapartida_str,
                            **({"override_apto": override} if override else {})
                        })
                    if cdeb: add_legado(cdeb, 'D')
                    if ccred: add_legado(ccred, 'C')
            except Exception as e_legado:
                print(f"Aviso: Erro ao ler LANCAMENTO_CONTABIL: {e_legado}")
    
            if not empreendimentos:
                empreendimentos = [{"id": empreendimento_id or 0, "nome": f"CC {empreendimento_id}" if empreendimento_id else "GERAL", "cc": empreendimento_id or 0, "vendas": []}]

            resultados = []
            for emp in empreendimentos:
                cc = emp["cc"]
                
                # --- INJEÇÃO VIRTUAL EXTRACONTÁBIL (VULCANO) ---
                contas_virtuais = {}
                def inject_virtual_entry(conta_id, valor, natureza, historico, logica="", saldo_ant=0.0, lote_id="Geral"):
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
                            "empreendimento_nome": nome_emp,   # ← chave para filtro do Racional
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
                        
                        # Gera chave única, estável e reprodutível baseada no conteúdo
                        import hashlib
                        stable_str = f"{ano}_{mes}_{conta_id}_{natureza}_{v_float}_{historico}"
                        chv_hash = hashlib.md5(stable_str.encode('utf-8')).hexdigest()[:12]
                        chave_v2 = f"VU2_{chv_hash}"
                        
                        override = memoria_arraste.get(chave_v2)
                        
                        contas_virtuais[conta_id]["detalhes"].append({
                            "chave": chave_v2,
                            "lote_id": str(lote_id).strip(),
                            "data": f"{last_day:02d}/{int(mes):02d}/{ano} (Sim)",
                            "historico": historico,
                            "natureza": natureza,
                            "valor": v_float,
                            "virtual": True,
                            "logica": logica,
                            **({"override_apto": override} if override else {})
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
    
    
                nome_emp = str(emp.get("nome") or "").strip()

                # ═══════════════════════════════════════════════════════════════
                # ETAPA 1: CUSTO GASTO GLOBAL — REGRA GERAL por tipo de obra
                # ═══════════════════════════════════════════════════════════════
                # REGRA: Para contas configuradas como CONTAESTAND (obra em andamento)
                # ou CONTAESTCON (obra concluida) no cadastro de EMPREENDIMENTO:
                #   - COM CC → gastos vem do LCTOGER filtrado pelo Centro de Custo
                #              (obra em construcao: Stuttgart CC=35, conta 5639, etc.)
                #   - SEM CC → gastos vem do LCTOGER filtrado pela propria conta de estoque
                #              (obras concluidas ou projetos sem CC configurado)
                # Esta regra garante que a conta de estoque SEMPRE receba o saldo
                # correto independentemente de haver vendas/recebimentos no periodo.
                ob_concluida = str(emp.get("obra_concluida", "N")).strip().upper() == 'S'
                c_estcon_raw = emp.get("conta_estcon") if ob_concluida else emp.get("conta_estand")
                c_estoque_inj = int(c_estcon_raw) if c_estcon_raw else None

                custo_gasto_anterior = 0.0
                custo_gasto_vigente  = 0.0
                mov_debito_mes = 0.0
                mov_credito_mes = 0.0
                mov_debito_mes       = 0.0
                mov_credito_mes      = 0.0

                if emp["cc"]:
                    # COM CC: usa LCTOGER/CC — filtro idêntico ao endpoint analítico.
                    # custo_anterior = acumulado ATÉ (exclusive) o início do mês
                    # custo_vigente  = acumulado ATÉ (exclusive) o fim do mês (inclui o mês corrente)
                    cur_q.execute("""
                        SELECT
                            SUM(CASE WHEN G.DATALCTOCTB <  CAST(? AS DATE)
                                     THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_anterior,
                            SUM(CASE WHEN G.DATALCTOCTB <  CAST(? AS DATE)
                                     THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_vigente,
                            SUM(CASE WHEN G.DATALCTOCTB >= CAST(? AS DATE) AND G.DATALCTOCTB < CAST(? AS DATE) AND G.NATURLCTOCTB = 1 THEN G.VALORLCTOGER ELSE 0 END) AS mov_debito_mes,
                            SUM(CASE WHEN G.DATALCTOCTB >= CAST(? AS DATE) AND G.DATALCTOCTB < CAST(? AS DATE) AND G.NATURLCTOCTB = -1 THEN G.VALORLCTOGER ELSE 0 END) AS mov_credito_mes
                        FROM LCTOGER G
                        JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                                      AND C.CHAVELCTOCTB  = G.CHAVELCTOCTB
                        WHERE G.CODIGOEMPRESA      = ?
                          AND G.CODIGOCENTROCUSTO  = ?
                          AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                    """, (data_inicio_mes_atual, data_fim_mes_atual, data_inicio_mes_atual, data_fim_mes_atual, data_inicio_mes_atual, data_fim_mes_atual,
                          empresa_id, emp["cc"]))
                    _r = cur_q.fetchone()
                    custo_gasto_anterior = float(_r[0] or 0.0)
                    custo_gasto_vigente  = float(_r[1] or 0.0)
                    mov_debito_mes = float(_r[2] or 0.0)
                    mov_credito_mes = float(_r[3] or 0.0)
                    print(f"[ESTOQUE/CC] {nome_emp[:35]} CC={emp['cc']} "
                          f"ant={custo_gasto_anterior:,.0f} vig={custo_gasto_vigente:,.0f} "
                          f"mov={custo_gasto_vigente-custo_gasto_anterior:,.0f}")
                          
                    if nome_emp in receitas_meta:
                        receitas_meta[nome_emp]["custo_gasto_vigente"] = custo_gasto_vigente

                elif c_estoque_inj:
                    # SEM CC: fallback pela conta de estoque debitada no LCTOGER.
                    # Mesmo padrão: anterior < inicio_mes, vigente < fim_mes.
                    cur_q.execute("""
                        SELECT
                            SUM(CASE WHEN G.DATALCTOCTB <  CAST(? AS DATE)
                                     THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_anterior,
                            SUM(CASE WHEN G.DATALCTOCTB <  CAST(? AS DATE)
                                     THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_vigente,
                            SUM(CASE WHEN G.DATALCTOCTB >= CAST(? AS DATE) AND G.DATALCTOCTB < CAST(? AS DATE) AND G.NATURLCTOCTB = 1 THEN G.VALORLCTOGER ELSE 0 END) AS mov_debito_mes,
                            SUM(CASE WHEN G.DATALCTOCTB >= CAST(? AS DATE) AND G.DATALCTOCTB < CAST(? AS DATE) AND G.NATURLCTOCTB = -1 THEN G.VALORLCTOGER ELSE 0 END) AS mov_credito_mes
                        FROM LCTOGER G
                        JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                                      AND C.CHAVELCTOCTB  = G.CHAVELCTOCTB
                        WHERE G.CODIGOEMPRESA = ?
                          AND C.CONTACTBDEB   = ?
                          AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                    """, (data_inicio_mes_atual, data_fim_mes_atual, data_inicio_mes_atual, data_fim_mes_atual, data_inicio_mes_atual, data_fim_mes_atual,
                          empresa_id, c_estoque_inj))
                    _r = cur_q.fetchone()
                    custo_gasto_anterior = float(_r[0] or 0.0)
                    custo_gasto_vigente  = float(_r[1] or 0.0)
                    mov_debito_mes = float(_r[2] or 0.0)
                    mov_credito_mes = float(_r[3] or 0.0)
                    print(f"[ESTOQUE/CONTA] {nome_emp[:35]} conta={c_estoque_inj} "
                          f"ant={custo_gasto_anterior:,.0f} vig={custo_gasto_vigente:,.0f}")
                    
                    if nome_emp in receitas_meta:
                        receitas_meta[nome_emp]["custo_gasto_vigente"] = custo_gasto_vigente

                # ═══════════════════════════════════════════════════════════════
                # ETAPA 2: POC NATIVO
                # ═══════════════════════════════════════════════════════════════
                poc_acumulado_vigente = 0.0
                poc_acumulado_anterior = 0.0
                # ob_concluida ja definido acima na ETAPA 1
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

                # ── COMPOSIÇÃO DO ESTOQUE (INJEÇÃO DE GASTOS FÍSICOS) ──
                # SEMPRE executada: os gastos do LCTOGER pelo CC do empreendimento devem
                # aparecer na conta de estoque independentemente de o empreendimento ter
                # ═══════════════════════════════════════════════════════════════
                # ETAPA 3: INJECAO DE ESTOQUE — REGRA GERAL (SEMPRE executada)
                # ═══════════════════════════════════════════════════════════════
                # Para toda conta configurada como CONTAESTAND ou CONTAESTCON,
                # o saldo de gastos incorridos e injetado como Debito Virtual.
                # Independe de haver vendas, recebimentos ou meta_emp no periodo.
                c_custo   = emp.get("conta_custo") or 99999
                c_estoque = c_estoque_inj or 99999  # definido na ETAPA 1
                fonte_str = f"CC {emp['cc']}" if emp["cc"] else f"conta {c_estoque}"

                injected_any = False
                mov_gasto = custo_gasto_vigente - custo_gasto_anterior
                if abs(mov_debito_mes) < 0.01 and abs(mov_credito_mes) < 0.01 and abs(custo_gasto_anterior) > 0.01:
                    inject_virtual_entry(
                        c_estoque, 0.0, 'D',
                        f"Saldo Obra {nome_emp} ({fonte_str})",
                        logica="Saldo Anterior transportado (sem movimento no mes atual)",
                        saldo_ant=custo_gasto_anterior
                    )
                    injected_any = True
                
                if abs(mov_debito_mes) > 0.01:
                    inject_virtual_entry(
                        c_estoque, mov_debito_mes, 'D',
                        f"Gastos Incorridos {nome_emp} ({fonte_str} - Débitos)",
                        logica=f"Débitos brutos da obra.",
                        saldo_ant=custo_gasto_anterior if not injected_any else 0.0,
                        lote_id=f"FISICO_{emp['id']}"
                    )
                    inject_virtual_entry(
                        int(emp.get("conta_caixa") or 99999), mov_debito_mes, 'C',
                        f"Contrapartida Gastos Incorridos {nome_emp} ({fonte_str})",
                        logica="Contrapartida (Saída de Caixa/Bancos ou Fornecedores)",
                        saldo_ant=0.0,
                        lote_id=f"FISICO_{emp['id']}"
                    )
                    injected_any = True
                    print(f"[ESTOQUE-INJECT] {nome_emp[:35]} -> conta={c_estoque} nat=D mov={abs(mov_debito_mes):,.0f}")

                if abs(mov_credito_mes) > 0.01:
                    inject_virtual_entry(
                        c_estoque, mov_credito_mes, 'C',
                        f"Gastos Incorridos {nome_emp} ({fonte_str} - Estornos/Créditos)",
                        logica=f"Créditos brutos da obra.",
                        saldo_ant=custo_gasto_anterior if not injected_any else 0.0,
                        lote_id=f"FISICO_{emp['id']}"
                    )
                    inject_virtual_entry(
                        int(emp.get("conta_caixa") or 99999), mov_credito_mes, 'D',
                        f"Contrapartida Gastos Incorridos {nome_emp} ({fonte_str} - Estornos)",
                        logica="Contrapartida (Entrada de Caixa/Bancos ou Fornecedores)",
                        saldo_ant=0.0,
                        lote_id=f"FISICO_{emp['id']}"
                    )
                    print(f"[ESTOQUE-INJECT] {nome_emp[:35]} -> conta={c_estoque} nat=C mov={abs(mov_credito_mes):,.0f}")

                    # ── INJECAO NO LADO FISICO (coluna Questor) — LANÇAMENTOS INDIVIDUAIS ──
                    # Os gastos do LCTOGER/CC são a fonte física dos custos de obra.
                    # Em vez de um único lançamento agregado sintético, buscamos os
                    # lançamentos INDIVIDUAIS do LCTOGER para exibição na aba Razão/Órfãos.
                    # Query IDÊNTICA à usada no fechamento de custos (api_custos_sincronizar_totalizadores).
                    _last_d = calendar.monthrange(int(ano), int(mes))[1]

                    if c_estoque not in contas_fisicas_empresa:
                        _cl_est = plano.get(c_estoque, {}).get("classif", "")
                        _nm_est = plano.get(c_estoque, {}).get("nome", "Desconhecida")
                        contas_fisicas_empresa[c_estoque] = {
                            "conta": c_estoque,
                            "nome": f"{_cl_est} - {_nm_est}" if _cl_est else _nm_est,
                            "classif": _cl_est,
                            "saldo_anterior": custo_gasto_anterior,
                            "movimento_debito": 0.0,
                            "movimento_credito": 0.0,
                            "movimento_liquido": 0.0,
                            "saldo_final": 0.0,
                            "detalhes": []
                        }
                    else:
                        # Conta já existe (passagem suplementar LCTOCTB) —
                        # substituir o saldo_anterior pelo valor do CC que é a
                        # fonte canônica para contas de construção em andamento.
                        contas_fisicas_empresa[c_estoque]["detalhes"] = []   # limpa detalhes anteriores
                        contas_fisicas_empresa[c_estoque]["saldo_anterior"] = custo_gasto_anterior
                        contas_fisicas_empresa[c_estoque]["movimento_debito"] = 0.0
                        contas_fisicas_empresa[c_estoque]["movimento_credito"] = 0.0
                        contas_fisicas_empresa[c_estoque]["movimento_liquido"] = 0.0

                    cf = contas_fisicas_empresa[c_estoque]

                    # Busca lançamentos individuais do mês pelo CC — mesma query do fechamento de custos
                    try:
                        cur_q.execute("""
                            SELECT G.CHAVELCTOCTB, G.DATALCTOCTB,
                                   G.VALORLCTOGER * G.NATURLCTOCTB AS VALOR_LIQUIDO,
                                   CAST(C.COMPLHIST AS BLOB SUB_TYPE 0),
                                   H.DESCRHISTCTB, G.NATURLCTOCTB
                            FROM LCTOGER G
                            JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                                          AND C.CHAVELCTOCTB   = G.CHAVELCTOCTB
                            LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
                            WHERE G.CODIGOEMPRESA    = ?
                              AND G.CODIGOCENTROCUSTO = ?
                              AND G.DATALCTOCTB >= CAST(? AS DATE)
                              AND G.DATALCTOCTB <  CAST(? AS DATE)
                              AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                            ORDER BY G.DATALCTOCTB ASC
                        """, (empresa_id, emp["cc"], data_inicio_mes_atual, data_fim_mes_atual))
                        lctoger_rows = cur_q.fetchall()
                    except Exception as _e_lc:
                        print(f"[AVISO] busca LCTOGER individual CC={emp['cc']}: {_e_lc}")
                        lctoger_rows = []

                    if lctoger_rows:
                        for (chave_lc, dt_lc, val_liq, hist_raw_lc, descr_hist_lc, nat_lc) in lctoger_rows:
                            v_lc = float(val_liq or 0)
                            if isinstance(hist_raw_lc, (bytes, bytearray)):
                                compl_lc = hist_raw_lc.decode("cp1252", "ignore")
                            elif hasattr(hist_raw_lc, "read"):
                                compl_lc = hist_raw_lc.read().decode("cp1252", "ignore")
                            else:
                                compl_lc = str(hist_raw_lc or "")
                            descr_lc = str(descr_hist_lc or "").strip()
                            hist_lc  = f"{descr_lc} {compl_lc}".strip()
                            hist_lc = _append_apto_if_matched(hist_lc)

                            if v_lc >= 0:
                                nat_str = "D"
                                cf["movimento_debito"]  += v_lc
                                cf["movimento_liquido"] += v_lc
                            else:
                                nat_str = "C"
                                cf["movimento_credito"] += abs(v_lc)
                                cf["movimento_liquido"] -= abs(v_lc)

                            dt_fmt = dt_lc.strftime('%d/%m/%Y') if hasattr(dt_lc, 'strftime') else str(dt_lc)
                            override = memoria_arraste.get(str(chave_lc).strip())
                            cf["detalhes"].append({
                                "chave":     str(chave_lc),
                                "data":      dt_fmt,
                                "historico": hist_lc,
                                "natureza":  nat_str,
                                "valor":     abs(v_lc),
                                "origem":    "LCTOGER_CC",
                                **({"override_apto": override} if override else {})
                            })
                    else:
                        # Fallback: sem lançamentos no mês mas há movimento acumulado → sintético
                        if abs(mov_gasto) > 0.01:
                            last_day_mes = f"{_last_d:02d}/{int(mes):02d}/{int(ano)}"
                            if nat_gasto == 'D':
                                cf["movimento_debito"]  += abs(mov_gasto)
                                cf["movimento_liquido"] += abs(mov_gasto)
                            else:
                                cf["movimento_credito"] += abs(mov_gasto)
                                cf["movimento_liquido"] -= abs(mov_gasto)
                            cf["detalhes"].append({
                                "chave":     f"LCTOGER_CC{emp['cc']}",
                                "data":      f"{_last_d:02d}/{int(mes):02d}/{int(ano)}",
                                "historico": f"Gastos Obra {nome_emp} via {fonte_str} (aglutinado)",
                                "natureza":  nat_gasto,
                                "valor":     abs(mov_gasto),
                                "origem":    "LCTOGER_CC"
                            })

                    cf["saldo_final"] = cf["saldo_anterior"] + cf["movimento_liquido"]
                    print(f"[FISICO-CC-INJECT] conta={c_estoque} saldo_ant={custo_gasto_anterior:,.0f} "
                          f"lancamentos={len(lctoger_rows)} mov_liq={cf['movimento_liquido']:,.0f} "
                          f"saldo_final={cf['saldo_final']:,.0f}")


                if meta_emp:
                    vgv_global = meta_emp.get("vgv", 0.0) or 1.0
                    unidades = meta_emp.get("unidades", [])
                    
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
                            SELECT V.DESCUNIDIMOB, U.ID, U.METRAGEM, U.DESCRICAO
                            FROM VENDA V
                            JOIN VENDAUNIDADE VU ON VU.IDVENDA = V.ID
                            JOIN UNIDADE U ON U.ID = VU.IDUNIDADE
                            JOIN BLOCO B ON B.ID = U.IDBLOCO
                            WHERE B.IDEMPREENDIMENTO = ?
                        """, (emp["id"],))
                        area_unidades = {}
                        seen_uids_per_desc = {}
                        desc_unid_dominant_map = {}
                        
                        for r_desc, u_id, r_met, r_udesc in cur_v.fetchall():
                            if r_desc:
                                k = str(r_desc).strip()
                                if k not in area_unidades:
                                    area_unidades[k] = 0.0
                                    seen_uids_per_desc[k] = set()
                                    desc_unid_dominant_map[k] = {"met": -1.0, "name": k}
                                    
                                if u_id not in seen_uids_per_desc[k]:
                                    _met = float(r_met or 0.0)
                                    area_unidades[k] += _met
                                    seen_uids_per_desc[k].add(u_id)
                                    
                                    if _met > desc_unid_dominant_map[k]["met"]:
                                        desc_unid_dominant_map[k]["met"] = _met
                                        _u_name = (r_udesc.decode('win1252', 'ignore') if isinstance(r_udesc, bytes) else str(r_udesc or '')).strip()
                                        desc_unid_dominant_map[k]["name"] = _u_name
                        
                        cur_v.execute("SELECT SUM(U.METRAGEM) FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = ?", (emp["id"],))
                        area_row = cur_v.fetchone()
                        total_area_emp = float(area_row[0]) if area_row and area_row[0] else 1.0
                    except Exception as eval_e:
                        print("Erro lendo metragem das unidades:", eval_e)
                        area_unidades = {}
                        total_area_emp = 1.0
    
                    unidades = meta_emp.get("unidades", [])
                    unidades_com_caixa = {str(u["unidade"]).strip(): u for u in unidades}
                    
                    data_ini_mes_ctb = f"{ano}-{str(mes).zfill(2)}-01"
                    data_fim_mes_ctb = f"{ano+1}-01-01" if int(mes) == 12 else f"{ano}-{str(int(mes)+1).zfill(2)}-01"
                    target_ym = f"{str(ano).zfill(4)}-{str(mes).zfill(2)}"
                    
                    try:
                        _cur_vendas = conn_vulcano.cursor()
                        _cur_vendas.execute("""
                            SELECT DESCUNIDIMOB, TOTALVENDA, DTOPER, DATADISTRATO, DISTRATO
                            FROM VENDA
                            WHERE IDEMPREENDIMENTO = ?
                              AND DTOPER < CAST(? AS DATE)
                        """, (emp["id"], data_fim_mes_ctb))
                        todas_vendas = _cur_vendas.fetchall()
                        _cur_vendas.close()
                    except Exception as _e_ven:
                        print(f"Erro consultando todas as vendas em graph logic: {_e_ven}")
                        todas_vendas = []
                        
                    for v_row in todas_vendas:
                        uni_raw, vgv_venda, dt_ven, dt_dis, distrato_flag = v_row[0], v_row[1], v_row[2], v_row[3], v_row[4]
                        uni_nome_raw = (uni_raw.decode('win1252', 'ignore') if isinstance(uni_raw, bytes) else str(uni_raw or '')).strip()
                        if not uni_nome_raw: continue
                        
                        # Apply dominant unit name to fix Kanban groupings (e.g. "290 / Vaga..." -> "APTO 1801")
                        uni_nome = desc_unid_dominant_map.get(uni_nome_raw, {}).get("name", uni_nome_raw)
                        
                        dt_dis_str = str(dt_dis)[:10] if dt_dis else ""
                        distrato_ym = dt_dis_str[:7] if len(dt_dis_str) >= 7 else ""
                        _flag = distrato_flag.decode('win1252','ignore') if isinstance(distrato_flag, bytes) else str(distrato_flag or "N")
                        is_distrato_s = _flag.strip().upper() == "S"
                        
                        # Se já estava distratada ANTES do mês-alvo, não processamos mais nada para a unidade
                        if distrato_ym and distrato_ym < target_ym:
                            continue
                            
                        # Resgata estado do pipeline de caixa usando raw name
                        uni_data = unidades_com_caixa.get(uni_nome_raw)
                        
                        if not uni_data:
                            # Unidade vendida mas sem movimento no caixa
                            uni_data = {
                                "unidade": uni_nome_raw,
                                "vgv": float(vgv_venda or 0.0),
                                "vgv_base": float(vgv_venda or 0.0),
                                "data_venda": str(dt_ven)[:10] if dt_ven else "",
                                "data_distrato": dt_dis_str,
                                "caixa_acumulado": 0.0,
                                "caixa_mes": 0.0,
                                "acrescimo_acumulado": 0.0,
                                "acrescimo_mes": 0.0,
                                "tributos_caixa_mes": 0.0,
                                "tributos_caixa_acumulado": 0.0,
                                "tributos_soc_mes": 0.0,
                                "tributos_soc_acumulado": 0.0,
                                "soc_acumulado": 0.0,
                                "receita_soc_mes": 0.0,
                                "tributos_total": 0.0,
                                "pis": 0, "cofins": 0, "irpj": 0, "csll": 0, "ret": 0, "irpj_adicional": 0
                            }
                            
                            # Para garantir lucro acumulado ou receitas passadas que não vieram do caixa deste mês,
                            # o idéal é assumir que o 'caixa_acumulado' não importa para o rateio do CMV,
                            # pois o CMV usa a 'Fração Física'
                        
                        vgv_uni = uni_data["vgv"]
                        vgv_base = uni_data.get("vgv_base", vgv_uni)
                        if vgv_base <= 0: continue
                        
                        # --- IFRS 15: Detectar se a venda ocorreu NO mês-alvo ---
                        data_venda_str = uni_data.get("data_venda") or ""
                        venda_ym = data_venda_str[:7] if data_venda_str and len(data_venda_str) >= 7 else ""
                        is_nova_venda_mes_alvo = bool(venda_ym) and (venda_ym == target_ym)
                        is_venda_futura = bool(venda_ym) and (venda_ym > target_ym)
                        
                        is_novo_distrato_mes_alvo = bool(distrato_ym) and (distrato_ym == target_ym)
                        
                        if is_venda_futura:
                            continue
                            
                        # CUSTO ECONÔMICO (Fração Física / Metragem)
                        # O Custo já reflete a evolução física (foi gasto e medido). Deve-se aplicar apenas o Índice Comercial da unidade.
                        area_da_unidade = area_unidades.get(str(uni_nome_raw).strip(), 0.0)
                        fracao_fisica = (area_da_unidade / total_area_emp) if total_area_emp > 0 else 0.0
                        
                        custo_u_atual = 0.0 if is_novo_distrato_mes_alvo else (custo_gasto_vigente * fracao_fisica)
                        custo_u_ant = 0.0 if is_nova_venda_mes_alvo else (custo_gasto_anterior * fracao_fisica)
                            
                        mov_custo_u = custo_u_atual - custo_u_ant
                        
                        if abs(mov_custo_u) > 0.01 or abs(custo_u_ant) > 0.01:
                             nat_custo = 'D' if mov_custo_u >= 0 else 'C'
                             nat_est = 'C' if mov_custo_u >= 0 else 'D'
                             
                             if is_novo_distrato_mes_alvo and mov_custo_u < 0:
                                 hist_base = emp.get('hist_estorno_custo', 'ESTORNO CUSTO')
                                 hist_estoque = emp.get('hist_estorno_custo', 'ESTORNO CUSTO')
                             else:
                                 hist_base = emp.get('hist_aprcusto', 'Apropriação Custo')
                                 hist_estoque = "BAIXA ESTOQUE"
                                 
                             logica_custo = f"Unid {uni_nome}: Custo Acum CC ({custo_gasto_vigente:,.2f}) * Fração Área ({fracao_fisica*100:.2f}%) = {custo_u_atual:,.2f} - Ant [{custo_u_ant:,.2f}]{'  [NOVA VENDA MÊS]' if is_nova_venda_mes_alvo else ''}{'  [DISTRATO MÊS ALVO]' if is_novo_distrato_mes_alvo else ''}"
                             inject_virtual_entry(c_custo, abs(mov_custo_u), nat_custo, f"{hist_base} UNID {uni_nome}", logica=logica_custo, saldo_ant=custo_u_ant, lote_id=f"CUSTO_{uni_nome}")
                             inject_virtual_entry(c_estoque, abs(mov_custo_u), nat_est, f"{hist_estoque} UNID {uni_nome}", logica=logica_custo, saldo_ant=-custo_u_ant, lote_id=f"CUSTO_{uni_nome}")
    
                        # ── RECEBIMENTOS: Split Principal vs Variação Monetária ─────────────────────────
                        caixa_acum = uni_data["caixa_acumulado"]
                        caixa_mes = uni_data.get("caixa_mes", 0.0)
                        caixa_ant = caixa_acum - caixa_mes
                        
                        if abs(caixa_mes) > 0.01:
                             logica_caixa = f"Unid {uni_nome}: Integralização de Caixa/Banco no mês = {caixa_mes:,.2f}"
                             inject_virtual_entry(c_caixa_banco, abs(caixa_mes), 'D' if caixa_mes > 0 else 'C', f"Recebimento Caixa - Unid {uni_nome}", logica=logica_caixa, saldo_ant=0.0, lote_id=f"CAIXA_{uni_nome}")

                        if is_venda_futura:
                             rec_auferida_atual = 0.0
                             rec_auferida_ant = 0.0
                        else:
                             rec_auferida_atual = 0.0 if (bool(distrato_ym) and distrato_ym <= target_ym) else (vgv_uni * (poc_acumulado_vigente / 100.0))
                             rec_auferida_ant = 0.0 if is_nova_venda_mes_alvo else \
                                               vgv_base * (poc_acumulado_anterior / 100.0)
                        
                        # -----------------
                        # RECEITA DRE (Econômico)
                        mov_receita_auferida = rec_auferida_atual - rec_auferida_ant
                        logica_rec = f"Unid {uni_nome}: VGV ({vgv_uni:,.2f}) * POC ({poc_acumulado_vigente}%) = {rec_auferida_atual:,.2f} - Ant [{rec_auferida_ant:,.2f}]{'  [NOVA VENDA MÊS / ANT 0]' if is_nova_venda_mes_alvo else ''}{'  [DISTRATO MÊS ALVO]' if is_novo_distrato_mes_alvo else ''}"
                        if abs(mov_receita_auferida) > 0.01 or abs(rec_auferida_ant) > 0.01:
                             nat_rec = 'C' if mov_receita_auferida >= 0 else 'D'
                             nat_cli_rec = 'D' if mov_receita_auferida >= 0 else 'C'
                             hist_rec_to_use = emp.get('hist_distrato', 'Distrato') if is_novo_distrato_mes_alvo else emp.get('hist_venda', 'Receita POC')
                             hist_cli_to_use = emp.get('hist_distrato', 'Distrato') if is_novo_distrato_mes_alvo else emp.get('hist_venda', 'Faturamento')
                             inject_virtual_entry(c_rec, abs(mov_receita_auferida), nat_rec, f"{hist_rec_to_use} UNID {uni_nome}", logica=logica_rec, saldo_ant=-rec_auferida_ant, lote_id=f"RECEITA_{uni_nome}")
                             inject_virtual_entry(c_cli, abs(mov_receita_auferida), nat_cli_rec, f"{hist_cli_to_use} UNID {uni_nome}", logica=logica_rec, saldo_ant=rec_auferida_ant, lote_id=f"RECEITA_{uni_nome}")
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
                             inject_virtual_entry(c_cli, abs(mov_cli), nat_cli, f"{emp.get('hist_rec', 'Baixa Cliente')} UNID {uni_nome}", logica=logica_cli, saldo_ant=-cli_ant, lote_id=f"CAIXA_{uni_nome}")
                        
                        if abs(mov_adi) > 0.01 or abs(adi_ant) > 0.01:
                             nat_adi = 'C' if mov_adi > 0 else 'D'
                             inject_virtual_entry(c_adi, abs(mov_adi), nat_adi, f"{emp.get('hist_adi', 'Reconhecimento Adiantamento')} UNID {uni_nome}", logica=logica_cli, saldo_ant=-adi_ant, lote_id=f"CAIXA_{uni_nome}")
                             
                        # --- Variação Monetária: D Clientes/Adi (par completo) + C CONTAVARIACAO ---
                        # Ambas só são geradas JUNTAS (mesma condição) → garante par na Auditoria.
                        if variacao_configurada and acrescimo_mes > 0.01:
                             logica_var = (f"Unid {uni_nome}: Acréscimo/Variação Monetária recebida no mês "
                                          f"({acrescimo_mes:,.2f}). Débito em Clientes se principal ≤ rec. auferida, "
                                          f"senão Adiantamentos.")
                             conta_deb_var = c_cli if caixa_principal_acum <= rec_auferida_atual + 0.01 else c_adi
                             inject_virtual_entry(c_variacao, acrescimo_mes, 'C',
                                 f"{emp.get('hist_var', 'Variação Monetária')} UNID {uni_nome}",
                                 logica=logica_var, saldo_ant=0.0, lote_id=f"VARIACAO_{uni_nome}")
                             inject_virtual_entry(conta_deb_var, acrescimo_mes, 'D',
                                 f"{emp.get('hist_var', 'Variação Monetária')} UNID {uni_nome}",
                                 logica=logica_var, saldo_ant=0.0, lote_id=f"VARIACAO_{uni_nome}")
                             
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
                                uni_data_pq = next((u for u in meta_pq.get("unidades", []) if u["unidade"] == uni_nome_raw), {})
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
                                inject_virtual_entry(c_deb, v_base, nat_d, f"Despesa Tributária DRE (Base Faturamento) - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=(_trib_caixa_ant * peso_imp), lote_id=f"TRIB_DARF_{desc.strip()}_{uni_nome}")
                                inject_virtual_entry(c_cred, v_base, nat_c, f"Passivo/DARF Exigível (Faturamento) - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=-(_trib_caixa_ant * peso_imp), lote_id=f"TRIB_DARF_{desc.strip()}_{uni_nome}")
                            
                            # 2. Ajuste Diferido (DRE Avançou > Caixa recebido = Criar Passivo Extra)
                            if abs(m_dif) > 0.01:
                                c_deb = cfg.get("CONTA_DEB_IMP_REC_PASSIVO_SOC") or 99999
                                c_cred = cfg.get("CONTA_CRED_IMP_REC_PASSIVO_SOC") or 99999
                                nat_d = 'D' if m_dif > 0 else 'C'
                                nat_c = 'C' if m_dif > 0 else 'D'
                                inject_virtual_entry(c_deb, abs(m_dif), nat_d, f"Provisão Tributo Diferido - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=(_t_dif_ant * peso_imp), lote_id=f"TRIB_DIF_{desc.strip()}_{uni_nome}")
                                inject_virtual_entry(c_cred, abs(m_dif), nat_c, f"Passivo Tributo Diferido - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=-(_t_dif_ant * peso_imp), lote_id=f"TRIB_DIF_{desc.strip()}_{uni_nome}")
                                
                            # 3. Ajuste Antecipado (Caixa recebido > DRE Avançou = Reduzir Despesa via Ativo)
                            if abs(m_ant) > 0.01:
                                c_deb = cfg.get("CONTA_DEB_IMP_APROP_ATIVO") or 99999 
                                c_cred = cfg.get("CONTA_DEB_IMP_SOBRE_VENDA") or 99999 # <-- Correção vital! Creditar a DESPESA para anular o excesso, preservar o DARF físico!
                                nat_d = 'D' if m_ant > 0 else 'C'
                                nat_c = 'C' if m_ant > 0 else 'D'
                                inject_virtual_entry(c_deb, abs(m_ant), nat_d, f"Tributo Antecipado (Ativo) - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=(_t_ant_ant * peso_imp), lote_id=f"TRIB_ANT_{desc.strip()}_{uni_nome}")
                                inject_virtual_entry(c_cred, abs(m_ant), nat_c, f"Estorno Excesso Despesa Trib - {desc} Unid {uni_nome}", logica=logica_imp, saldo_ant=-(_t_ant_ant * peso_imp), lote_id=f"TRIB_ANT_{desc.strip()}_{uni_nome}")

                        # ── ESTORNO DE RET NO DISTRATO ────────────────────────────────────
                        # Se a unidade foi distratada NESTE mês-alvo e o empreendimento usa RET,
                        # gera D:conta_cred_darf (4995) / C:conta_antecipado (4845 se obra em
                        # construção, 4996 se obra concluída) proporcional ao caixa acumulado.
                        # Base legal: Lei 10.931/2004 + CPC 47 estorno de ativo/passivo tributário.
                        if distrato_ym == target_ym and is_distrato_s:
                            try:
                                for imp_cfg in valid_confs:
                                    desc = imp_cfg.get("DESCRICAO")
                                    # Para o estorno retroativo do distrato, a base real inabalada no modelo de dados
                                    # é o `caixa_acumulado` (ele retém o histórico mesmo que o VGV da unidade vire 0).
                                    # O `trib_detalhe_caixa_acumulado` quebra quando não há movimento novo no mês.
                                    aliquota = float(imp_cfg.get("ALIQUOTA", 0)) / 100.0
                                    caixa_real_acumulado = uni_data.get("caixa_acumulado", 0.0)
                                    trib_acum_ant = caixa_real_acumulado * aliquota

                                    if trib_acum_ant > 0.01:
                                        c_deb_est  = imp_cfg.get("CONTA_CRED_IMP_REC_DARF") or 4995   # debita RET a Recolher (reduz passivo)
                                        obra_conc  = str(emp.get("obra_concluida") or "N").upper() == "S"
                                        c_cred_est = (imp_cfg.get("CONTA_DEB_IMP_SOBRE_VENDA") or 4996  # obra concluída → estorna despesa
                                                      if obra_conc
                                                      else imp_cfg.get("CONTA_DEB_IMP_APROP_ATIVO") or 4845)  # obra em andamento → estorna ativo diferido
                                        
                                        hist_dist  = f"ESTORNO {desc} DISTRATO UNID {uni_nome}"
                                        logica_dist = (f"Distrato em {dt_dis_str} — estorno {desc} acumulado até {target_ym}: "
                                                       f"R${trib_acum_ant:,.2f} base R${caixa_real_acumulado:,.2f}. Obra: {obra_conc}. "
                                                       f"D:{c_deb_est} / C:{c_cred_est}.")
                                        
                                        inject_virtual_entry(c_deb_est,  trib_acum_ant, 'D', hist_dist, logica=logica_dist, saldo_ant=0.0, lote_id=f"DISTRATO_{desc.strip()}_{uni_nome}")
                                        inject_virtual_entry(c_cred_est, trib_acum_ant, 'C', hist_dist, logica=logica_dist, saldo_ant=0.0, lote_id=f"DISTRATO_{desc.strip()}_{uni_nome}")
                                        print(f"[{desc}-DISTRATO] {uni_nome} | D:{c_deb_est} C:{c_cred_est} | R${trib_acum_ant:,.2f} | {dt_dis_str}")
                            except Exception as _e_ret_dist:
                                print(f"[{desc}-DISTRATO] Erro no estorno para {uni_nome}: {_e_ret_dist}")

    
                # Fecha saldo_final de todas as contas virtuais APÓS todas as injeções (incluindo novas vendas)
                for c, data in contas_virtuais.items():
                    data["saldo_final"] = data["saldo_anterior"] + data["movimento_liquido"]
    
                eh_primeiro = len(resultados) == 0
    
                if len(contas_fisicas_empresa) > 0 or len(contas_virtuais) > 0:
                    resultados.append({
                        "empreendimento_id": emp.get("id"),
                        "empreendimento_nome": emp.get("nome", "Desconhecido"),
                        "total_anterior_fisico": total_anterior_fisico if eh_primeiro else 0.0,
                        "total_movimento_fisico": total_movimento_fisico if eh_primeiro else 0.0,
                        "total_final_fisico": total_final_fisico if eh_primeiro else 0.0,
                        "contas_fisicas": [],  # Sera preenchido no final do loop
                        "contas_legado": [],   # Sera preenchido no final do loop
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
                        
                        
                        # --- ENCONTRAR CONTA CLIENTES DEPOSITO BANCARIO DINAMICAMENTE DA MEMORIA ---
                        c_deb_deposito = 99999
                        c_deb_deposito = 4910
                                    
                        c_cred_receita = 230
                        
                        for estab in todos_estabs:
                            v_loc = loc_mes.get(estab, 0.0)
                            v_loc_trim = loc_trim.get(estab, 0.0)
                            
                            v_loc_ant = loc_ant.get(estab, 0.0)
                            v_loc_ant_trim = loc_ant_trim.get(estab, 0.0)
                            
                            nome_filial = f"Estab {estab} (SCP/Filial)" if estab > 1 else "Matriz"
                            
                            # --- INJECAO DA RECEITA BRUTA MENSAL E CAIXA DE LOCAÇÃO ---
                            if abs(v_loc) > 0.01 or abs(v_loc_ant) > 0.01:
                                inject_loc_entry(c_deb_deposito, v_loc, 'D', f"Recebimento Locação {nome_filial}", saldo_ant=v_loc_ant, logica_str=f"Recebimento Mês Bruto: R$ {v_loc:,.2f}")
                                inject_loc_entry(c_cred_receita, v_loc, 'C', f"Receita de Locação {nome_filial}", saldo_ant=-v_loc_ant, logica_str=f"Receita Mês Bruto: R$ {v_loc:,.2f}")
                            # ---------------------------------------------------------
                            
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
                
            # --- POST-PROCESSING: Contrapartidas para Contas Virtuais ---
            for res in resultados:
                lotes_v = {}
                for cv in res.get("contas_virtuais", []):
                    for det in cv.get("detalhes", []):
                        lid = det.get("lote_id")
                        if not lid or lid == "Geral": continue
                        if lid not in lotes_v: lotes_v[lid] = {"D": [], "C": []}
                        lotes_v[lid][det["natureza"]].append(cv["conta"])
                
                for cv in res.get("contas_virtuais", []):
                    for det in cv.get("detalhes", []):
                        lid = det.get("lote_id")
                        if not lid or lid == "Geral": continue
                        nat = det["natureza"]
                        oposto = "C" if nat == "D" else "D"
                        copts = lotes_v.get(lid, {}).get(oposto, [])
                        if copts:
                            copt_id = copts[0]
                            copt_nome = plano.get(copt_id, {}).get("nome", "") if copt_id else ""
                            det["contrapartida"] = f"{copt_id} - {copt_nome}" if copt_nome else str(copt_id or "")

            # ATRIBUICAO FINAL DAS CONTAS FISICAS GLOBAIS
            # O frontend precisa de todas as contas fisicas (LCTOGER/LCTOCTB + injeções de CC)
            # agrupadas na primeira posicao do resultado. Como os empreendimentos podem
            # injetar gastos no dict global durante o loop, nos convertemos e atribuimos
            # somente apos o termino absoluto do processamento.
            if resultados:
                resultados[0]["contas_fisicas"] = list(contas_fisicas_empresa.values())
                resultados[0]["contas_legado"] = list(contas_legado_empresa.values())
            return {"data": resultados, "dashboard_meta": receitas_meta}
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
    