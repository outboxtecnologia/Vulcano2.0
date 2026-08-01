import firebirdsql
import datetime
import calendar

def get_db_conn(db_type):
    if db_type == "vulcano":
        return firebirdsql.connect(
            host="localhost",
            database=r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB",
            port=3050,
            user="SYSDBA",
            password="masterkey",
            charset="WIN1252"
        )
    elif db_type == "questor":
        return firebirdsql.connect(
            host="localhost",
            database=r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB",
            port=3050,
            user="SYSDBA",
            password="masterkey",
            charset="WIN1252"
        )

def _so_digitos(s):
    return "".join(ch for ch in str(s or "") if ch.isdigit())


def _mask_doc(digits):
    """Formata CPF/CNPJ com máscara — padrão do CPFCNPJADQU no Questor."""
    d = _so_digitos(digits)
    if len(d) == 11:
        return f"{d[0:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"
    if len(d) == 14:
        return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"
    return str(digits or "").strip()


def _dec(v):
    if isinstance(v, bytes):
        return v.decode("cp1252", "ignore").strip()
    return str(v).strip() if v is not None else ""


# Parcela pertence ao F200 quando NÃO pertence ao RET (obra optante a partir de
# DATAINICIORET vai pro bloco 1800 — processar_ret; o resto é F200 comum).
_F200_PARCELA_FORA_DO_RET = """
      AND (E.ID IS NULL OR E.RET IS NULL OR E.RET <> 'S'
           OR (E.DATAINICIORET IS NOT NULL AND R.DATA < E.DATAINICIORET))
"""


def processar_f200(empresa_id: int, ano: int, mes: int, dry_run: bool = True, get_conn=None):
    """
    F200 do SPED Contribuições: receita imobiliária mensal por unidade vendida,
    espelhando o padrão do escritório em EFDUNIDIMOBILIARIA (cadastro, PK
    empresa+estab+numcadimob) e EFDUNIDIMOBVENDIDA (movimento, PK +compreceb).

    - Exclui recebimentos de obras optantes do RET (vão pelo bloco 1800).
    - De-para unidade→Questor pelos campos-espelho da VENDA (NUMCADIMOB/CODIGOESTAB).
    - Regime (0,65/3,00 presumido × 1,65/7,60 real), tipodebito e operacaofis são
      herdados do histórico da própria unidade (fallback: último lançamento da empresa).
    - Idempotente: unidade já lançada na competência é pulada (JA_LANCADO).

    Status: PRONTO | NOVO_CADASTRO (insere o pai junto) | JA_LANCADO |
            SEM_ESPELHO (VENDA sem NUMCADIMOB) | SEM_TEMPLATE (empresa nunca usou F200).
    """
    if get_conn is None:
        return {"success": False, "error": "processar_f200 requer get_conn do main.py (dispatch vulcano/questor)."}

    dt_comp = datetime.date(ano, mes, 1)

    # 1) vulcano: recebimentos do mês e acumulado, agregados por venda (2 queries no total)
    conn_v = get_conn("vulcano")
    try:
        cur_v = conn_v.cursor()
        cur_v.execute(f"""
            SELECT V.ID, V.NUMCADIMOB, V.CODIGOESTAB, V.TOTALVENDA, V.DTOPER,
                   V.INDOPER, V.UNIDIMOB, V.DESCUNIDIMOB, V.INDNATEMP, V.CNPJ,
                   C.NOME, E.NOME, SUM(R.TOTALPAGO),
                   SUM(COALESCE(R.VALORVARIACAO, 0)), E.CUSTOORCADO
            FROM RECEBER R
            JOIN VENDA V ON R.IDVENDA = V.ID
            JOIN CLIENTE C ON V.ID_CLIENTE = C.ID
            LEFT JOIN EMPREENDIMENTO E ON V.IDEMPREENDIMENTO = E.ID
            WHERE V.CODIGOEMPRESA = ?
              AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
              AND R.TOTALPAGO > 0
              AND EXTRACT(YEAR FROM R.DATA) = ?
              AND EXTRACT(MONTH FROM R.DATA) = ?
              {_F200_PARCELA_FORA_DO_RET}
            GROUP BY V.ID, V.NUMCADIMOB, V.CODIGOESTAB, V.TOTALVENDA, V.DTOPER,
                     V.INDOPER, V.UNIDIMOB, V.DESCUNIDIMOB, V.INDNATEMP, V.CNPJ,
                     C.NOME, E.NOME, E.CUSTOORCADO
        """, (empresa_id, ano, mes))
        vendas_mes = cur_v.fetchall()

        cur_v.execute(f"""
            SELECT R.IDVENDA, SUM(R.TOTALPAGO)
            FROM RECEBER R
            JOIN VENDA V ON R.IDVENDA = V.ID
            LEFT JOIN EMPREENDIMENTO E ON V.IDEMPREENDIMENTO = E.ID
            WHERE V.CODIGOEMPRESA = ?
              AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
              AND R.TOTALPAGO > 0
              AND R.DATA < ?
              {_F200_PARCELA_FORA_DO_RET}
            GROUP BY R.IDVENDA
        """, (empresa_id, dt_comp))
        acum_vulcano = {r[0]: float(r[1] or 0) for r in cur_v.fetchall()}
    except Exception as e:
        return {"success": False, "error": f"vulcano: {e}"}
    finally:
        conn_v.close()

    conn_q = None
    try:
        # 2) Questor: histórico da vendida (template de regime + encadeamento do acumulado),
        #    cadastro pai existente e o que já está lançado na competência
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()

        cur_q.execute("""
            SELECT CODIGOESTAB, NUMCADIMOB, COMPRECEB, VLRECACUM, VLTOTREC,
                   ALIQPIS, ALIQCOFINS, TIPODEBITO, CODIGOOPERACAOFISIRPJ,
                   CODIGOOPERACAOFISCSLL, FORMAFATURAMENTO
            FROM EFDUNIDIMOBVENDIDA
            WHERE CODIGOEMPRESA = ?
            ORDER BY COMPRECEB
        """, (empresa_id,))
        hist_unit, chain, lancados_comp, template_empresa = {}, {}, set(), None
        for r in cur_q.fetchall():
            k = (int(r[0]), int(r[1]))
            row = {
                "compreceb": r[2], "vlrecacum": float(r[3] or 0), "vltotrec": float(r[4] or 0),
                "aliqpis": float(r[5] or 0), "aliqcofins": float(r[6] or 0),
                "tipodebito": _dec(r[7]), "opfis_irpj": r[8], "opfis_csll": r[9],
                "formafat": _dec(r[10]) or "501",
            }
            hist_unit[k] = row          # último da unidade (ORDER BY compreceb)
            template_empresa = row      # último da empresa
            if row["compreceb"] == dt_comp:
                lancados_comp.add(k)
            elif row["compreceb"] < dt_comp:
                chain[k] = row          # último ANTES da competência (encadeia o acumulado)

        cur_q.execute("""
            SELECT CODIGOESTAB, NUMCADIMOB FROM EFDUNIDIMOBILIARIA WHERE CODIGOEMPRESA = ?
        """, (empresa_id,))
        cadastro = {(int(r[0]), int(r[1])) for r in cur_q.fetchall()}

        # 3) Monta os itens (1 por unidade com recebimento no mês)
        itens = []
        for v in vendas_mes:
            (vid, numcad, estab, totalvenda, dtoper, indoper, unidimob,
             descunid, indnatemp, cnpj, cliente, obra, rec_mes,
             variacao_mes, custo_orcado) = v
            rec_mes = round(float(rec_mes or 0), 2)
            variacao_mes = round(float(variacao_mes or 0), 2)
            if rec_mes <= 0:
                continue
            estab = int(estab or 1)
            numcad = int(numcad) if numcad else None
            k = (estab, numcad) if numcad else None

            tpl = (hist_unit.get(k) if k else None) or template_empresa
            if numcad is None:
                status = "SEM_ESPELHO"
            elif k in lancados_comp:
                status = "JA_LANCADO"
            elif tpl is None:
                status = "SEM_TEMPLATE"
            elif k not in cadastro:
                status = "NOVO_CADASTRO"
            else:
                status = "PRONTO"

            prev = chain.get(k) if k else None
            acum = round(prev["vlrecacum"] + prev["vltotrec"], 2) if prev else round(acum_vulcano.get(vid, 0.0), 2)
            totalvenda = round(float(totalvenda or 0), 2)
            aliqpis = tpl["aliqpis"] if tpl else 0.65
            aliqcofins = tpl["aliqcofins"] if tpl else 3.00

            itens.append({
                "venda_id": vid, "status": status,
                "codigoestab": estab, "numcadimob": numcad,
                "unidade": _dec(descunid), "obra": _dec(obra), "cliente": _dec(cliente),
                "cnpj_adquirente": _mask_doc(cnpj), "dtoper": dtoper.isoformat() if dtoper else None,
                "indoper": _dec(indoper) or "04", "unidimob": _dec(unidimob) or "04",
                "indnatemp": int(indnatemp) if indnatemp is not None else 3,
                "compreceb": dt_comp.isoformat(),
                "variacao": variacao_mes, "valor_parcela": round(rec_mes - variacao_mes, 2),
                "custo_orcado": round(float(custo_orcado or 0), 2),
                "vltotvend": totalvenda, "vlrecacum": acum, "vltotrec": rec_mes,
                "percrecreceb": round((acum + rec_mes) / totalvenda * 100, 2) if totalvenda > 0 else 0.0,
                "vlbc": rec_mes,
                "aliqpis": aliqpis, "vlpis": round(rec_mes * aliqpis / 100, 2),
                "aliqcofins": aliqcofins, "vlcofins": round(rec_mes * aliqcofins / 100, 2),
                "tipodebito": tpl["tipodebito"] if tpl else "",
                "formafaturamento": tpl["formafat"] if tpl else "501",
                "opfis_irpj": tpl["opfis_irpj"] if tpl else None,
                "opfis_csll": tpl["opfis_csll"] if tpl else None,
            })

        if dry_run:
            return {"success": True, "data": itens}

        # 4) Commit: insere PRONTO e NOVO_CADASTRO (pai antes da filha; nunca duplica)
        gravaveis = [i for i in itens if i["status"] in ("PRONTO", "NOVO_CADASTRO")]
        for item in gravaveis:
            if item["status"] == "NOVO_CADASTRO":
                doc = _so_digitos(item["cnpj_adquirente"])
                cur_q.execute("""
                    INSERT INTO EFDUNIDIMOBILIARIA (
                        CODIGOEMPRESA, CODIGOESTAB, NUMCADIMOB, IDENTEMP, INDOPER, UNIDIMOB,
                        DESCUNIDIMOB, NUMCONT, CODIGOPESSOA, TIPOINSCR, CPFCNPJADQU, DTOPER,
                        VLCUSTOORC, INDNATEMP, INFCOMP, CODIGOTABCTBFIS, ORIGEMDADO
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    empresa_id, item["codigoestab"], item["numcadimob"],
                    (item["obra"] or "").upper()[:100], item["indoper"], item["unidimob"],
                    item["unidade"][:90], None, None,
                    2 if len(doc) == 14 else 1, item["cnpj_adquirente"][:18],
                    item["dtoper"], 0.00, item["indnatemp"], item["cliente"][:90], None, 2,
                ))
            cur_q.execute("""
                INSERT INTO EFDUNIDIMOBVENDIDA (
                    CODIGOEMPRESA, CODIGOESTAB, NUMCADIMOB, COMPRECEB,
                    VLTOTVEND, VLRECACUM, VLTOTREC, PERCRECRECEB, VLBC,
                    CSTPIS, ALIQPIS, VLPIS, CSTCOFINS, ALIQCOFINS, VLCOFINS,
                    TIPODEBITO, FORMAFATURAMENTO, CONSIDERAPROPORC, APURAECF,
                    CODIGOOPERACAOFISIRPJ, CODIGOOPERACAOFISCSLL, CODIGOTABCTBFIS, ORIGEMDADO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                empresa_id, item["codigoestab"], item["numcadimob"], dt_comp,
                item["vltotvend"], item["vlrecacum"], item["vltotrec"],
                item["percrecreceb"], item["vlbc"],
                1, item["aliqpis"], item["vlpis"], 1, item["aliqcofins"], item["vlcofins"],
                item["tipodebito"], item["formafaturamento"], "1", "1",
                item["opfis_irpj"], item["opfis_csll"], None, 2,
            ))
        conn_q.commit()

        pulados = sum(1 for i in itens if i["status"] == "JA_LANCADO")
        problemas = sum(1 for i in itens if i["status"] in ("SEM_ESPELHO", "SEM_TEMPLATE"))
        msg = f"{len(gravaveis)} registro(s) F200 inseridos no Questor (competência {mes:02d}/{ano})."
        if pulados:
            msg += f" {pulados} já lançado(s) — pulados."
        if problemas:
            msg += f" {problemas} unidade(s) sem espelho/template — exigem intervenção manual."
        return {"success": True, "message": msg, "inseridos": len(gravaveis),
                "ja_lancados": pulados, "com_problema": problemas}

    except Exception as e:
        try:
            if conn_q:
                conn_q.rollback()
        except Exception:
            pass
        return {"success": False, "error": f"questor: {e}"}
    finally:
        if conn_q:
            conn_q.close()

# Composição da guia unificada RET (Lei 10.931/2004, art. 4º; 1% = PMCMV, art. 4º §6º-7º).
# Alíquotas fora da tabela são rateadas proporcionalmente à composição dos 4%.
_RET_SPLIT = {
    4.0: {"pis": 0.37, "cofins": 1.71, "csll": 0.66, "irpj": 1.26},
    1.0: {"pis": 0.09, "cofins": 0.44, "csll": 0.16, "irpj": 0.31},
}


def _norm_nome(s):
    """Normaliza nome de obra p/ casar EMPREENDIMENTO.NOME (vulcano) com INCIMOB (Questor)."""
    import unicodedata
    if s is None:
        return ""
    if isinstance(s, bytes):
        s = s.decode("cp1252", "ignore")
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.upper().split())


def processar_ret(empresa_id: int, ano: int, mes: int, dry_run: bool = True, get_conn=None):
    """
    RET Lei 10.931: agrega os recebimentos das obras OPTANTES (EMPREENDIMENTO.RET='S',
    respeitando DATAINICIORET e ALIQRET por obra) na competência e monta/insere os
    registros EFDINCORPIMOBRET no Questor (bloco 1800 do SPED Contribuições).

    O de-para obra→(CODIGOESTAB, CNPJINCIMOB, imposto) é derivado do histórico já
    lançado em EFDINCORPIMOBRET (match por nome normalizado). Status por obra:
      PRONTO      — calculada e mapeada; será inserida no commit
      JA_LANCADO  — já existe linha p/ o estab nessa competência (nunca duplica)
      SEM_DE_PARA — obra sem histórico no Questor; exige 1º lançamento manual

    `get_conn` é o factory do main.py (vulcano=Firebird, questor=Postgres traduzido).
    """
    if get_conn is None:
        return {"success": False, "error": "processar_ret requer get_conn do main.py (dispatch vulcano/questor)."}

    dt_comp = datetime.date(ano, mes, 1)
    dt_recuni = datetime.date(ano + 1, 1, 20) if mes == 12 else datetime.date(ano, mes + 1, 20)

    # 1) Receitas da competência por obra optante (vulcano/Firebird, regime pelo vencimento baixado)
    conn_v = get_conn("vulcano")
    try:
        cur_v = conn_v.cursor()
        cur_v.execute("""
            SELECT E.ID, E.NOME, E.ALIQRET,
                   SUM(R.TOTALPAGO) AS TOTAL,
                   SUM(COALESCE(R.VALORVARIACAO, 0)) AS VARIACAO
            FROM RECEBER R
            JOIN VENDA V ON R.IDVENDA = V.ID
            JOIN EMPREENDIMENTO E ON V.IDEMPREENDIMENTO = E.ID
            WHERE V.CODIGOEMPRESA = ?
              AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
              AND R.TOTALPAGO > 0
              AND EXTRACT(YEAR FROM R.DATA) = ?
              AND EXTRACT(MONTH FROM R.DATA) = ?
              AND E.RET = 'S'
              AND (E.DATAINICIORET IS NULL OR R.DATA >= E.DATAINICIORET)
            GROUP BY E.ID, E.NOME, E.ALIQRET
        """, (empresa_id, ano, mes))
        obras = cur_v.fetchall()
    except Exception as e:
        return {"success": False, "error": f"vulcano: {e}"}
    finally:
        conn_v.close()

    conn_q = None
    try:
        # 2) De-para obra→estab pelo histórico do Questor + o que já existe na competência
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()
        cur_q.execute("""
            SELECT INCIMOB, CODIGOESTAB, CNPJINCIMOB, CODIGOIMPOSTO, VARIACAOIMPOSTO,
                   FORMAFATURAMENTO, CODIGOTABCTBFIS
            FROM EFDINCORPIMOBRET
            WHERE CODIGOEMPRESA = ?
            ORDER BY DATALCTOFIS
        """, (empresa_id,))
        de_para = {}
        for r in cur_q.fetchall():  # ORDER BY data: o lançamento mais recente vence
            de_para[_norm_nome(r[0])] = {
                "incimob": str(r[0]).strip(), "codigoestab": r[1], "cnpjincimob": str(r[2]).strip(),
                "codigoimposto": r[3], "variacaoimposto": r[4],
                "formafaturamento": r[5], "codigotabctbfis": r[6],
            }

        cur_q.execute("""
            SELECT CODIGOESTAB, INCIMOB, SEQ
            FROM EFDINCORPIMOBRET
            WHERE CODIGOEMPRESA = ? AND DATALCTOFIS = ?
        """, (empresa_id, dt_comp))
        ja_lancados, max_seq = set(), {}
        for estab, incimob, seq in cur_q.fetchall():
            ja_lancados.add((estab, _norm_nome(incimob)))
            max_seq[estab] = max(max_seq.get(estab, 0), int(seq or 0))

        # 3) Monta os itens
        itens = []
        for ob in obras:
            nome = ob[1].decode("cp1252", "ignore") if isinstance(ob[1], bytes) else str(ob[1] or "")
            nome = nome.strip()
            aliq = float(ob[2]) if ob[2] is not None else 4.0
            bc = round(float(ob[3] or 0), 2)
            fin = round(float(ob[4] or 0), 2)
            if bc <= 0:
                continue

            split = _RET_SPLIT.get(round(aliq, 2)) or {
                k: round(v * aliq / 4.0, 4) for k, v in _RET_SPLIT[4.0].items()
            }
            mapa = de_para.get(_norm_nome(nome))
            if not mapa:
                status = "SEM_DE_PARA"
            elif (mapa["codigoestab"], _norm_nome(mapa["incimob"])) in ja_lancados:
                status = "JA_LANCADO"
            else:
                status = "PRONTO"

            itens.append({
                "obra_id": ob[0], "unidade": nome, "status": status,
                "codigoestab": mapa["codigoestab"] if mapa else None,
                "cnpjincimob": mapa["cnpjincimob"] if mapa else None,
                "incimob": mapa["incimob"] if mapa else nome,
                "datalctofis": dt_comp.isoformat(), "dtrecuni": dt_recuni.isoformat(),
                "receita_principal": round(bc - fin, 2), "receita_financeira": fin,
                "base_calculo": bc, "aliqret": aliq,
                "pis": round(bc * split["pis"] / 100, 2),
                "cofins": round(bc * split["cofins"] / 100, 2),
                "csll": round(bc * split["csll"] / 100, 2),
                "irpj": round(bc * split["irpj"] / 100, 2),
                "total_ret": round(bc * aliq / 100, 2),
            })

        if dry_run:
            return {"success": True, "data": itens}

        # 4) Commit: insere só os PRONTO (idempotente — JA_LANCADO nunca duplica)
        prontos = [i for i in itens if i["status"] == "PRONTO"]
        for item in prontos:
            estab = item["codigoestab"]
            max_seq[estab] = max_seq.get(estab, 0) + 1
            cur_q.execute("""
                INSERT INTO EFDINCORPIMOBRET (
                    CODIGOEMPRESA, CODIGOESTAB, DATALCTOFIS, SEQ, CNPJINCIMOB, INCIMOB,
                    RECRECEBRET, RECFINRET, BCRET, ALIQRET, VLRECUNI, DTRECUNI,
                    CODIGOIMPOSTO, VARIACAOIMPOSTO, FORMAFATURAMENTO, CODIGOTABCTBFIS, ORIGEMDADO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                empresa_id, estab, dt_comp, max_seq[estab],
                item["cnpjincimob"], item["incimob"],
                item["receita_principal"], item["receita_financeira"], item["base_calculo"],
                item["aliqret"], item["total_ret"], dt_recuni,
                de_para[_norm_nome(item["incimob"])]["codigoimposto"],
                de_para[_norm_nome(item["incimob"])]["variacaoimposto"],
                de_para[_norm_nome(item["incimob"])]["formafaturamento"],
                de_para[_norm_nome(item["incimob"])]["codigotabctbfis"],
                2,
            ))
        conn_q.commit()

        pulados = sum(1 for i in itens if i["status"] == "JA_LANCADO")
        sem_mapa = sum(1 for i in itens if i["status"] == "SEM_DE_PARA")
        msg = f"{len(prontos)} guia(s) RET inseridas no Questor (competência {mes:02d}/{ano})."
        if pulados:
            msg += f" {pulados} já lançada(s) — puladas."
        if sem_mapa:
            msg += f" {sem_mapa} obra(s) sem de-para no Questor — exigem 1º lançamento manual."
        return {"success": True, "message": msg, "inseridos": len(prontos),
                "ja_lancados": pulados, "sem_de_para": sem_mapa}

    except Exception as e:
        try:
            if conn_q:
                conn_q.rollback()
        except Exception:
            pass
        return {"success": False, "error": f"questor: {e}"}
    finally:
        if conn_q:
            conn_q.close()
