from langchain_core.tools import tool
import json
import os
import sys

# Importação lazy para evitar circular import
def _get_conn(tipo):
    # Importa get_conn do contexto do backend
    try:
        from main import get_conn
        return get_conn(tipo)
    except Exception as e:
        raise RuntimeError(f"Erro ao obter conexão {tipo}: {e}")

def _get_poc_db():
    """Retorna o path do banco SQLite de POC."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "poc_database.sqlite")


@tool
def analisar_lancamentos_questor(conta_alvo: str, empresa_id: int = 959, limite: int = 15) -> str:
    """Busca os últimos lançamentos contábeis no LCTOCTB do Questor para a conta indicada (ex: '5639').
    Retorna data, histórico, natureza (D/C) e valor. Use isso para verificar o que está fisicamente contabilizado."""
    try:
        # Extrai número da conta do texto "Conta 5639 - RECEITA DE VENDA"
        import re
        match = re.search(r'\b(\d{3,6})\b', conta_alvo)
        if not match:
            return json.dumps({"status": "error", "message": f"Não encontrei número de conta em: {conta_alvo}"})
        num_conta = int(match.group(1))

        conn = _get_conn("questor")
        cur = conn.cursor()
        cur.execute("""
            SELECT FIRST ? L.DATALCTOCTB, L.COMPLHIST, L.VALORLCTOCTB,
                   L.CONTACTBDEB, L.CONTACTBCRED
            FROM LCTOCTB L
            WHERE L.CODIGOEMPRESA = ?
              AND (L.CONTACTBDEB = ? OR L.CONTACTBCRED = ?)
              AND L.CODIGOORIGLCTOCTB <> 'ZZ'
            ORDER BY L.DATALCTOCTB DESC
        """, (limite, empresa_id, num_conta, num_conta))
        rows = cur.fetchall()
        conn.close()

        lancamentos = []
        for r in rows:
            nat = "D" if int(r[3] or 0) == num_conta else "C"
            lancamentos.append({
                "data": str(r[0])[:10] if r[0] else "",
                "historico": str(r[1] or ""),
                "valor": float(r[2] or 0),
                "natureza": nat,
                "conta_deb": int(r[3] or 0),
                "conta_cred": int(r[4] or 0),
            })

        saldo_deb = sum(l["valor"] for l in lancamentos if l["natureza"] == "D")
        saldo_cred = sum(l["valor"] for l in lancamentos if l["natureza"] == "C")

        return json.dumps({
            "ferramenta": "analisar_lancamentos_questor",
            "status": "success",
            "conta": num_conta,
            "total_lancamentos": len(lancamentos),
            "saldo_debito_amostra": round(saldo_deb, 2),
            "saldo_credito_amostra": round(saldo_cred, 2),
            "lancamentos": lancamentos[:10]
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def verificar_receitas_custos_poc(conta_alvo: str, empresa_id: int = 959) -> str:
    """Busca a POC atual e o histórico de reconhecimento de receitas/custos no banco SQLite poc_database.
    Retorna POC por empreendimento, VGV acumulado e receita reconhecida. Use para contas de resultado IFRS 15."""
    try:
        import sqlite3, re
        db_path = _get_poc_db()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Pega os empreendimentos mais relevantes
        rows = conn.execute("""
            SELECT e.id, e.nome, e.percentual_concluido, e.vgv_total,
                   SUM(COALESCE(v.vgv_unidade, 0)) AS vgv_vendido
            FROM empreendimento e
            LEFT JOIN venda v ON v.id_empreendimento = e.id
            WHERE e.codigo_empresa = ?
            GROUP BY e.id
            ORDER BY e.percentual_concluido DESC
            LIMIT 10
        """, (empresa_id,)).fetchall()

        empreendimentos = [dict(r) for r in rows]

        # Receitas reconhecidas (se tabela existir)
        try:
            rec_rows = conn.execute("""
                SELECT mes, ano, SUM(valor_periodo) AS total_receita
                FROM poc_receitas
                WHERE codigo_empresa = ?
                GROUP BY ano, mes
                ORDER BY ano DESC, mes DESC
                LIMIT 6
            """, (empresa_id,)).fetchall()
            receitas_recentes = [dict(r) for r in rec_rows]
        except Exception:
            receitas_recentes = []

        conn.close()

        return json.dumps({
            "ferramenta": "verificar_receitas_custos_poc",
            "status": "success",
            "empreendimentos": empreendimentos,
            "receitas_ultimos_meses": receitas_recentes,
            "interpretacao": (
                "POC acima de 100% indica obras concluídas. "
                "Receita reconhecida = VGV_vendido * POC. "
                "Divergência pode ser causada por reconhecimento retroativo ou arredondamento."
            )
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def buscar_conta_no_plano(conta_alvo: str, empresa_id: int = 959) -> str:
    """Busca no Plano de Contas do Questor informações sobre a conta: nome, natureza, grupo.
    Também procura contas similares (mesmo radical) para investigar lançamentos em subcontas."""
    try:
        import re
        match = re.search(r'\b(\d{3,6})\b', conta_alvo)
        if not match:
            return json.dumps({"status": "error", "message": "Nenhum número de conta encontrado."})
        num_conta = int(match.group(1))
        prefixo = str(num_conta)[:3]

        conn = _get_conn("questor")
        cur = conn.cursor()

        # Conta específica
        cur.execute("""
            SELECT CONTACTB, DESCRCONTA, NATURSALDO
            FROM PLANOESPEC
            WHERE CODIGOEMPRESA = ? AND CONTACTB = ?
        """, (empresa_id, num_conta))
        conta_row = cur.fetchone()

        # Contas com mesmo radical (3 primeiros dígitos)
        cur.execute("""
            SELECT FIRST 15 CONTACTB, DESCRCONTA, NATURSALDO
            FROM PLANOESPEC
            WHERE CODIGOEMPRESA = ?
              AND CAST(CONTACTB AS VARCHAR(10)) STARTING WITH ?
            ORDER BY CONTACTB
        """, (empresa_id, prefixo))
        similares = [{"conta": int(r[0]), "nome": str(r[1] or ""), "natureza": str(r[2] or "")} for r in cur.fetchall()]
        conn.close()

        resultado = {
            "ferramenta": "buscar_conta_no_plano",
            "status": "success",
            "conta": num_conta,
            "conta_info": {
                "conta": num_conta,
                "nome": str(conta_row[1] or "") if conta_row else "Não encontrada",
                "natureza": str(conta_row[2] or "") if conta_row else ""
            } if conta_row else {"conta": num_conta, "nome": "Não encontrada"},
            "contas_grupo": similares
        }
        return json.dumps(resultado, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def buscar_proximidade_passivos_fiscais(conta_alvo: str, empresa_id: int = 959) -> str:
    """Para diferenças em contas de tributo ou passivo, varre o LCTOCTB do Questor procurando contas com saldo similar à divergência detectada.
    Use quando conta começa com 2 (passivo) ou for de tributos (IRPJ, CSLL, PIS, COFINS, ISS)."""
    try:
        import re
        match = re.search(r'\b(\d{3,6})\b', conta_alvo)
        conta_base = int(match.group(1)) if match else 0
        prefixo = str(conta_base)[:1]  # grupo (1=Ativo, 2=Passivo, 3=PL, 4=Receita, 5=Despesa)

        conn = _get_conn("questor")
        cur = conn.cursor()

        # Busca saldos movimentados das contas do mesmo grupo nos últimos 12 meses
        cur.execute("""
            SELECT L.CONTACTBDEB AS conta, SUM(L.VALORLCTOCTB) AS total_deb, COUNT(*) AS n
            FROM LCTOCTB L
            WHERE L.CODIGOEMPRESA = ?
              AND L.CODIGOORIGLCTOCTB <> 'ZZ'
              AND CAST(L.CONTACTBDEB AS VARCHAR(10)) STARTING WITH ?
            GROUP BY L.CONTACTBDEB
            HAVING SUM(L.VALORLCTOCTB) > 1000
            ORDER BY total_deb DESC
            FETCH FIRST 10 ROWS ONLY
        """, (empresa_id, prefixo))
        contas_com_saldo = []
        for r in cur.fetchall():
            contas_com_saldo.append({"conta": int(r[0] or 0), "saldo_debito": round(float(r[1] or 0), 2), "n_lancamentos": int(r[2] or 0)})

        conn.close()
        return json.dumps({
            "ferramenta": "buscar_proximidade_passivos_fiscais",
            "status": "success",
            "conta_alvo": conta_base,
            "grupo_pesquisado": prefixo,
            "contas_com_maior_saldo": contas_com_saldo,
            "interpretacao": "Verifique se há reclassificação necessária entre subcontas do mesmo grupo."
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def analisar_estoque_lctoger(conta_alvo: str, empresa_id: int = 959,
                              cc_empreendimento: int = None,
                              data_ini: str = None, data_fim: str = None) -> str:
    """Para contas de ESTOQUE DE OBRA (classif 1.x — ex: IMÓVEIS A CONCLUIR), consulta LCTOGER
    para obter o saldo REAL acumulado e todos os lançamentos do empreendimento.

    PADRÃO IMÓVEIS EM CONSTRUÇÃO: gastos de obra são lançados DIRETAMENTE no LCTOGER pelo
    Centro de Custo do empreendimento (parâmetro cc_empreendimento), independentemente da conta
    contábil. O cc_empreendimento é o identificador-chave: ex. CC=35 para Res. Stuttgart.

    Modos de consulta:
    - COM cc_empreendimento: retorna TODOS os lançamentos do CC (independente da conta).
      Este é o modo correto para contas de imóveis a concluir (1.x).
    - SEM cc_empreendimento: filtra apenas pelos lançamentos onde a conta é débito ou crédito.

    Parâmetros opcionais data_ini / data_fim no formato 'YYYY-MM-DD' para filtrar por período.
    Use esta ferramenta ANTES de qualquer outra para contas 1.x."""
    try:
        import re
        match = re.search(r'\b(\d{3,6})\b', conta_alvo)
        if not match:
            return json.dumps({"status": "error", "message": f"Número de conta não encontrado em: {conta_alvo}"})
        num_conta = int(match.group(1))

        conn = _get_conn("questor")
        cur = conn.cursor()

        filtro_data = ""
        params_data: list = []
        if data_ini:
            filtro_data += " AND C.DATALCTOCTB >= CAST(? AS DATE)"
            params_data.append(data_ini)
        if data_fim:
            filtro_data += " AND C.DATALCTOCTB < CAST(? AS DATE)"
            params_data.append(data_fim)

        # ── Modo CC: todos os lançamentos do empreendimento (padrão de obra) ──
        if cc_empreendimento is not None:
            params_cc = [empresa_id, cc_empreendimento] + params_data

            cur.execute(f"""
                SELECT
                    SUM(CASE WHEN G.NATURLCTOCTB =  1 THEN G.VALORLCTOGER ELSE 0 END),
                    SUM(CASE WHEN G.NATURLCTOCTB = -1 THEN G.VALORLCTOGER ELSE 0 END),
                    COUNT(*),
                    COUNT(DISTINCT C.CONTACTBDEB)
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                               AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                WHERE G.CODIGOEMPRESA = ?
                  AND G.CODIGOCENTROCUSTO = ?
                  AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                  {filtro_data}
            """, tuple(params_cc))
            row = cur.fetchone()
            total_deb  = float(row[0] or 0)
            total_cred = float(row[1] or 0)
            n_lanc     = int(row[2] or 0)
            n_contas   = int(row[3] or 0)

            # Top 15 contas mais debitadas no CC
            cur.execute(f"""
                SELECT FIRST 15
                    C.CONTACTBDEB, COUNT(*) AS n, SUM(G.VALORLCTOGER) AS soma
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                               AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                WHERE G.CODIGOEMPRESA = ?
                  AND G.CODIGOCENTROCUSTO = ?
                  AND G.NATURLCTOCTB = 1
                  AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                  {filtro_data}
                GROUP BY C.CONTACTBDEB
                ORDER BY soma DESC
            """, tuple(params_cc))
            contas_mais_debitadas = [
                {"conta_deb": int(r[0] or 0), "n_lancamentos": int(r[1]), "soma_debito": round(float(r[2] or 0), 2)}
                for r in cur.fetchall()
            ]

            # 50 lançamentos mais recentes do CC (todas as contas)
            cur.execute(f"""
                SELECT FIRST 50
                    C.DATALCTOCTB, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0),
                    G.VALORLCTOGER, G.NATURLCTOCTB,
                    C.CONTACTBDEB, C.CONTACTBCRED, G.CODIGOCENTROCUSTO,
                    H.DESCRHISTCTB
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CODIGOEMPRESA  = G.CODIGOEMPRESA
                               AND C.CHAVELCTOCTB  = G.CHAVELCTOCTB
                LEFT JOIN HISTCTB H ON H.CODIGOEMPRESA = C.CODIGOEMPRESA
                               AND H.CODIGOHISTCTB = C.CODIGOHISTCTB
                WHERE G.CODIGOEMPRESA = ?
                  AND G.CODIGOCENTROCUSTO = ?
                  AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                  {filtro_data}
                ORDER BY C.DATALCTOCTB DESC
            """, tuple(params_cc))

            lancamentos = []
            for r in cur.fetchall():
                compl = r[1].decode('cp1252', 'ignore') if isinstance(r[1], (bytes, bytearray)) else str(r[1] or "")
                descr = str(r[7] or "").strip()
                hist  = f"{descr} {compl}".strip()
                nat   = "D" if r[3] == 1 else "C"
                lancamentos.append({
                    "data":       str(r[0])[:10] if r[0] else "",
                    "historico":  hist[:140],
                    "valor":      round(float(r[2] or 0), 2),
                    "natureza":   nat,
                    "conta_deb":  int(r[4] or 0),
                    "conta_cred": int(r[5] or 0),
                    "cc":         r[6],
                })

            conn.close()
            conta_presente = any(l["conta_deb"] == num_conta or l["conta_cred"] == num_conta for l in lancamentos)
            return json.dumps({
                "ferramenta": "analisar_estoque_lctoger",
                "modo": "cc_empreendimento",
                "status": "success",
                "conta_alvo": num_conta,
                "cc_empreendimento": cc_empreendimento,
                "saldo_debito_cc": round(total_deb, 2),
                "saldo_credito_cc": round(total_cred, 2),
                "saldo_liquido_cc": round(total_deb - total_cred, 2),
                "n_lancamentos_total_cc": n_lanc,
                "n_contas_debitadas_distintas": n_contas,
                "conta_alvo_presente_nos_lancamentos": conta_presente,
                "contas_mais_debitadas_no_cc": contas_mais_debitadas,
                "lancamentos_recentes": lancamentos,
                "interpretacao": (
                    f"CC {cc_empreendimento}: {n_lanc} lançamentos no LCTOGER. "
                    + (f"Conta {num_conta} PRESENTE nos lançamentos abertos." if conta_presente
                       else f"ATENÇÃO: conta {num_conta} NÃO aparece nos 50 mais recentes — verifique CC ou período.")
                    + f" {n_contas} contas distintas debitadas neste CC."
                ),
            }, ensure_ascii=False)

        # ── Modo Conta (legado): filtra por conta DEB/CRED ────────────────────
        else:
            params_saldo = [empresa_id, num_conta, num_conta] + params_data

            cur.execute(f"""
                SELECT
                    SUM(CASE WHEN G.NATURLCTOCTB =  1 THEN G.VALORLCTOGER ELSE 0 END),
                    SUM(CASE WHEN G.NATURLCTOCTB = -1 THEN G.VALORLCTOGER ELSE 0 END),
                    COUNT(*),
                    COUNT(DISTINCT G.CODIGOCENTROCUSTO)
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                               AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                WHERE G.CODIGOEMPRESA = ?
                  AND (C.CONTACTBDEB = ? OR C.CONTACTBCRED = ?)
                  AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                  {filtro_data}
            """, tuple(params_saldo))
            row = cur.fetchone()
            total_deb  = float(row[0] or 0)
            total_cred = float(row[1] or 0)
            n_lanc     = int(row[2] or 0)
            n_cc       = int(row[3] or 0)

            cur.execute(f"""
                SELECT FIRST 10
                    G.CODIGOCENTROCUSTO, COUNT(*), SUM(G.VALORLCTOGER)
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                               AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                WHERE G.CODIGOEMPRESA = ?
                  AND C.CONTACTBDEB = ?
                  AND G.NATURLCTOCTB = 1
                  AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                  {filtro_data}
                GROUP BY G.CODIGOCENTROCUSTO
                ORDER BY SUM(G.VALORLCTOGER) DESC
            """, tuple([empresa_id, num_conta] + params_data))
            centros_com_debito = [
                {"cc": r[0], "n_lancamentos": int(r[1]), "soma_debito": round(float(r[2] or 0), 2)}
                for r in cur.fetchall()
            ]

            cur.execute(f"""
                SELECT FIRST 30
                    C.DATALCTOCTB, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0),
                    G.VALORLCTOGER, G.NATURLCTOCTB,
                    C.CONTACTBDEB, C.CONTACTBCRED, G.CODIGOCENTROCUSTO
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                               AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                WHERE G.CODIGOEMPRESA = ?
                  AND (C.CONTACTBDEB = ? OR C.CONTACTBCRED = ?)
                  AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                  {filtro_data}
                ORDER BY C.DATALCTOCTB DESC
            """, tuple(params_saldo))

            lancamentos = []
            for r in cur.fetchall():
                compl = r[1].decode('cp1252', 'ignore') if isinstance(r[1], (bytes, bytearray)) else str(r[1] or "")
                nat   = "D" if r[3] == 1 else "C"
                lancamentos.append({
                    "data":       str(r[0])[:10] if r[0] else "",
                    "historico":  compl.strip()[:120],
                    "valor":      round(float(r[2] or 0), 2),
                    "natureza":   nat,
                    "conta_deb":  int(r[4] or 0),
                    "conta_cred": int(r[5] or 0),
                    "cc":         r[6],
                })

            conn.close()
            tem_debitos_cc = len(centros_com_debito) > 0
            return json.dumps({
                "ferramenta": "analisar_estoque_lctoger",
                "modo": "por_conta",
                "status": "success",
                "conta": num_conta,
                "saldo_debito_real": round(total_deb, 2),
                "saldo_credito_real": round(total_cred, 2),
                "saldo_liquido_real": round(total_deb - total_cred, 2),
                "n_lancamentos_total": n_lanc,
                "n_centros_custo_distintos": n_cc,
                "tem_debitos_cc": tem_debitos_cc,
                "centros_custo_com_debito": centros_com_debito,
                "lancamentos_recentes": lancamentos[:20],
                "interpretacao": (
                    "Débitos presentes por CC — Fechamento de Custos contabilizado."
                    if tem_debitos_cc else
                    "ATENÇÃO: Sem débitos por CC. Use cc_empreendimento para ver gastos de obra no LCTOGER."
                ),
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def agrupar_creditos_por_apto(conta_alvo: str, empresa_id: int = 959,
                               data_ini: str = None, data_fim: str = None) -> str:
    """Estilo Splink: agrupa os CRÉDITOS de uma conta de estoque por número de APTO
    extraído do COMPLHIST. Calcula o % de cada unidade no total de créditos e detecta
    o padrão de distribuição (uniforme = fração física esperada vs concentrado = anomalia).
    Use para confirmar se a baixa de estoque distribuiu corretamente entre as unidades.
    Parâmetros opcionais data_ini / data_fim no formato 'YYYY-MM-DD'."""
    try:
        import re, statistics
        match = re.search(r'\b(\d{3,6})\b', conta_alvo)
        if not match:
            return json.dumps({"status": "error", "message": "Número de conta não encontrado."})
        num_conta = int(match.group(1))

        conn = _get_conn("questor")
        cur = conn.cursor()

        filtro_data = ""
        params: list = [empresa_id, num_conta]
        if data_ini:
            filtro_data += " AND C.DATALCTOCTB >= CAST(? AS DATE)"
            params.append(data_ini)
        if data_fim:
            filtro_data += " AND C.DATALCTOCTB < CAST(? AS DATE)"
            params.append(data_fim)

        # Busca todos os créditos (NATURLCTOCTB = -1 → crédito na conta)
        cur.execute(f"""
            SELECT CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), G.VALORLCTOGER, C.DATALCTOCTB
            FROM LCTOGER G
            JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA
                           AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
            WHERE G.CODIGOEMPRESA = ?
              AND C.CONTACTBCRED = ?
              AND G.NATURLCTOCTB = -1
              AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
              {filtro_data}
            ORDER BY C.DATALCTOCTB DESC
        """, tuple(params))

        apto_grupos: dict = {}
        total_credito = 0.0
        apto_pattern = re.compile(r'\bAPT[O]?[\s\-]*(\d+)', re.IGNORECASE)

        for r in cur.fetchall():
            compl = r[0].decode('cp1252', 'ignore') if isinstance(r[0], (bytes, bytearray)) else str(r[0] or "")
            valor = float(r[1] or 0)
            data_str = str(r[2])[:10] if r[2] else ""
            total_credito += valor

            matches = apto_pattern.findall(compl)
            # Usa SEMPRE a última ocorrência (número real do apto, não do contrato)
            apto_key = f"APTO_{matches[-1]}" if matches else "SEM_APTO"

            if apto_key not in apto_grupos:
                apto_grupos[apto_key] = {"apto": apto_key, "valor_total": 0.0, "n_lancamentos": 0,
                                          "primeira_data": data_str, "ultima_data": data_str,
                                          "exemplo_historico": compl.strip()[:80]}
            g = apto_grupos[apto_key]
            g["valor_total"] += valor
            g["n_lancamentos"] += 1
            if data_str < g["primeira_data"]: g["primeira_data"] = data_str
            if data_str > g["ultima_data"]:   g["ultima_data"]   = data_str

        conn.close()

        # Calcula % e ordena
        for g in apto_grupos.values():
            g["pct_do_total"] = round((g["valor_total"] / total_credito * 100) if total_credito > 0 else 0, 2)
            g["valor_total"]  = round(g["valor_total"], 2)

        grupos_ord = sorted(
            [g for g in apto_grupos.values() if g["apto"] != "SEM_APTO"],
            key=lambda x: int(x["apto"].replace("APTO_", "")),
        )
        sem_apto = [g for g in apto_grupos.values() if g["apto"] == "SEM_APTO"]
        grupos_final = grupos_ord + sem_apto

        # Detecta padrão de distribuição (coeficiente de variação)
        valores_apto = [g["valor_total"] for g in grupos_ord if g["valor_total"] > 0]
        if len(valores_apto) >= 2:
            media = statistics.mean(valores_apto)
            desvio = statistics.stdev(valores_apto)
            coef_variacao = round(desvio / media, 4) if media > 0 else 0
            if coef_variacao < 0.30:
                padrao = "UNIFORME — distribuição equilibrada entre unidades (provável fração física correta)"
            elif coef_variacao < 0.60:
                padrao = "MODERADO — pequenas diferenças entre unidades (verificar metragens diferentes)"
            else:
                padrao = "CONCENTRADO — grande variação entre unidades (investigar unidades de valor atípico)"
        else:
            coef_variacao = 0
            padrao = "INSUFICIENTE — menos de 2 APTOs identificados para análise de padrão"

        return json.dumps({
            "ferramenta": "agrupar_creditos_por_apto",
            "status": "success",
            "conta": num_conta,
            "total_credito": round(total_credito, 2),
            "n_aptos_identificados": len(grupos_ord),
            "n_sem_apto": len(sem_apto),
            "coeficiente_variacao": coef_variacao,
            "padrao_distribuicao": padrao,
            "grupos": grupos_final,
            "interpretacao": (
                "Créditos com APTO identificado representam baixas de estoque por unidade. "
                "O % de cada APTO deve ser proporcional à sua fração de área sobre a área total do empreendimento. "
                "Divergências > 5% entre unidades com áreas similares indicam possível erro de cálculo."
            ),
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

