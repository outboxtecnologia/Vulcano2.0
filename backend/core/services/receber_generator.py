"""
receber_generator.py
====================
Motor unico de geracao de parcelas em RECEBER a partir da matriz de prazos
(VENDAFORMAPAGTOPRAZO). Serve o CLI (gerar_receber_vendas_sem_parcela.py) e os
endpoints /api/vulcano/gerar-parcelas e /api/vulcano/popular-receber-abertas.

A conexao vem SEMPRE por parametro (nunca e aberta aqui). E isso que permite o
mesmo codigo rodar com firebirdsql.connect() do CLI e com get_conn("vulcano") do
main.py sem duplicar query nem INSERT — que antes existiam em tres copias
divergentes (main.py, popular_receber_abertas.py, scratch/populate_receber.py).

MODOS
-----
  A  venda que nao possui NENHUMA linha em RECEBER -> gera a matriz inteira de
     prazos dela. Se a venda ja tem qualquer parcela, nao toca.
  B  parcelas orfas: prazo sem linha correspondente em RECEBER, inclusive de
     vendas ja parcialmente lancadas. Repara buracos no meio de uma venda.

  B contem A: toda venda sem nenhuma parcela tem todos os prazos orfaos. Rodar A
  e depois B nao duplica (o NOT EXISTS do B ja enxerga o que o A gravou), mas
  rodar B sozinho ja resolve o A junto.

  data_inicio/data_fim so valem no modo A? NAO — so valem no modo B. No modo A o
  contrato e "a matriz inteira da venda"; recortar por vencimento geraria parte
  das parcelas e deixaria a venda no exato estado intermediario que o modo B
  existe para reparar.

TRIGGERS DE RECEBER QUE IMPORTAM AQUI
-------------------------------------
  RECEBER_BI               atribui ID via GEN_RECEBER_ID quando ID vem null/0.
                           Por isso o INSERT daqui OMITE a coluna ID. Informar
                           MAX(ID)+1 na mao nao avanca o generator e quebra as
                           inserções seguintes do Vulcano legado com violacao de
                           PK.
  RECEBER_BIU0             arredonda totalpago/valorparcela/valorvariacao.
  RECEBER_AIUD10           soma new.totalpago em VENDAFORMAPAGTOPRAZO.VALOR_PAGO
                           (inofensivo aqui: gravamos TOTALPAGO = 0).
  RECEBER_BLOQUEIO_BIUD10  rejeita insert com DATA <= CONFIGURACAO_BLOQUEIO.
                           DATA_BLOQUEIO (MODULO=1) da empresa/estab. Erros por
                           linha sao tolerados e devolvidos em erros_detalhe.
"""
import json
import os
from datetime import datetime

# Teto de linhas por execucao. Cabe o modo A inteiro (~8.2k parcelas medidas em
# 2026-08) com folga e, a ~50-150 inserts/s, fecha em 1 a 3,5 min — o limite do
# que se tolera numa request sincrona. O modo B com todas as empresas (~310k) fica
# 31x acima e precisa ser fatiado por empresa/periodo, que e o comportamento certo:
# 310k parcelas vencidas desde 2015 nao devem entrar em um clique.
TETO_PARCELAS = 10_000

# Linhas devolvidas na amostra de conferencia. Os totais NAO saem daqui.
PREVIEW_MAX = 200

MODOS = ("A", "B")

_CRITERIO = {
    # Venda sem nenhuma parcela materializada.
    "A": "NOT EXISTS (SELECT 1 FROM RECEBER r WHERE r.IDVENDA = v.ID)",
    # Prazo sem linha correspondente, ainda nao quitado no legado.
    "B": ("NOT EXISTS (SELECT 1 FROM RECEBER r WHERE r.IDVENDAFORMAPAGTOPRAZO = vpp.ID)"
          " AND (vpp.VALOR_PAGO = 0 OR vpp.VALOR_PAGO IS NULL)"),
}


def fmt_int(valor):
    """Inteiro em pt-BR: 301396 -> '301.396'."""
    return f"{valor:,}".replace(",", ".")


def fmt_valor(valor):
    """Moeda em pt-BR: 1632855663.3 -> '1.632.855.663,30'. O replace direto de
    ',' por '.' estragaria o separador decimal."""
    return f"{valor:,.2f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def normalizar_modo(modo):
    m = (modo or "A").strip().upper()
    if m not in MODOS:
        raise ValueError(f"Modo invalido: {modo!r}. Use 'A' ou 'B'.")
    return m


def _iso(valor):
    """Data -> 'YYYY-MM-DD'. Nunca devolve datetime (o JSON da API e a ordenacao
    da tela trabalham com string; new Date() no front volta um dia por fuso)."""
    if valor is None:
        return None
    if hasattr(valor, "strftime"):
        return valor.strftime("%Y-%m-%d")
    return str(valor)[:10]


def montar_query(modo, empresa_id=None, data_inicio=None, data_fim=None, limite=None):
    """Devolve (sql, params). Só o FIRST N e interpolado — o Firebird nao aceita
    parametro ali — e passa por int() antes."""
    modo = normalizar_modo(modo)
    params = []
    filtros = [_CRITERIO[modo], "vfp.ATIVA = 'S'",
               "(v.DISTRATO IS NULL OR v.DISTRATO <> 'S')"]

    if empresa_id is not None:
        filtros.append("v.CODIGOEMPRESA = ?")
        params.append(int(empresa_id))

    # Recorte por vencimento so faz sentido no reparo pontual (modo B).
    if modo == "B":
        if data_inicio:
            filtros.append("vpp.DATA >= ?")
            params.append(str(data_inicio))
        if data_fim:
            filtros.append("vpp.DATA <= ?")
            params.append(str(data_fim))

    first = f"FIRST {int(limite)} " if limite else ""

    sql = f"""
        SELECT {first}
            vpp.ID          AS PRAZO_ID,
            vpp.DATA        AS VENCIMENTO,
            vpp.VALOR       AS VALOR_PARCELA,
            vfp.ID          AS IDVENDAFORMAPAGTO,
            vfp.DESCRICAO   AS OBS_DESCRICAO,
            vfp.IDVENDA     AS IDVENDA,
            v.ID_CLIENTE    AS ID_CLIENTE,
            v.CODIGOEMPRESA AS CODIGOEMPRESA,
            v.CODIGOESTAB   AS CODIGOESTAB
        FROM VENDAFORMAPAGTOPRAZO vpp
        JOIN VENDAFORMAPAGTO vfp ON vfp.ID = vpp.IDVENDAFORMAPAGTO
        JOIN VENDA v            ON v.ID   = vfp.IDVENDA
        WHERE {' AND '.join(filtros)}
        ORDER BY v.CODIGOEMPRESA, vfp.IDVENDA, vpp.DATA
    """
    return sql, params


def buscar_alvos(conn, modo="A", empresa_id=None, data_inicio=None,
                 data_fim=None, limite=None):
    """Linhas candidatas, normalizadas em dicts."""
    sql, params = montar_query(modo, empresa_id, data_inicio, data_fim, limite)
    cur = conn.cursor()
    cur.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def carregar_bloqueios(conn):
    """{(empresa, estab): 'YYYY-MM-DD'} de CONFIGURACAO_BLOQUEIO (MODULO=1).

    Best effort: serve so para avisar o operador antes da execucao. A defesa real
    e o try/except por linha em inserir(), porque a trigger e quem decide.
    Devolve None se a tabela nao existir ou mudar de forma.
    """
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT CODIGOEMPRESA, CODIGOESTAB, DATA_BLOQUEIO
            FROM CONFIGURACAO_BLOQUEIO WHERE MODULO = 1
        """)
        return {(r[0], r[1]): _iso(r[2]) for r in cur.fetchall()}
    except Exception:
        return None


def _bloqueada(alvo, bloqueios):
    if not bloqueios:
        return False
    limite = bloqueios.get((alvo.get("CODIGOEMPRESA"), alvo.get("CODIGOESTAB")))
    venc = _iso(alvo.get("VENCIMENTO"))
    return bool(limite and venc and venc <= limite)


def resumir(alvos, bloqueios=None):
    """Totais, quebra por empresa e amostra de conferencia.

    Os totais saem da lista inteira; `preview` e so amostra. A tela deve exibir
    valor_total daqui, nunca a soma das linhas visiveis.
    """
    vendas = {a["IDVENDA"] for a in alvos}
    empresas = {a["CODIGOEMPRESA"] for a in alvos}
    valor_total = sum(float(a["VALOR_PARCELA"] or 0) for a in alvos)
    vencs = sorted(v for v in (_iso(a["VENCIMENTO"]) for a in alvos) if v)

    por_empresa = {}
    for a in alvos:
        emp = a["CODIGOEMPRESA"]
        acc = por_empresa.setdefault(emp, {
            "empresa": emp, "vendas": set(), "parcelas": 0,
            "valor": 0.0, "venc_min": None, "venc_max": None,
        })
        acc["vendas"].add(a["IDVENDA"])
        acc["parcelas"] += 1
        acc["valor"] += float(a["VALOR_PARCELA"] or 0)
        venc = _iso(a["VENCIMENTO"])
        if venc:
            if acc["venc_min"] is None or venc < acc["venc_min"]:
                acc["venc_min"] = venc
            if acc["venc_max"] is None or venc > acc["venc_max"]:
                acc["venc_max"] = venc

    lista_empresas = sorted(
        ({**v, "vendas": len(v["vendas"])} for v in por_empresa.values()),
        key=lambda e: e["valor"], reverse=True,
    )

    preview = [{
        "prazo_id": a["PRAZO_ID"],
        "idvenda": a["IDVENDA"],
        "empresa": a["CODIGOEMPRESA"],
        "data": _iso(a["VENCIMENTO"]),
        "parcela": competencia(a["VENCIMENTO"]),
        "valor": float(a["VALOR_PARCELA"] or 0),
        "obs": str(a["OBS_DESCRICAO"] or "PARCELA")[:50],
        "bloqueada": _bloqueada(a, bloqueios),
    } for a in alvos[:PREVIEW_MAX]]

    return {
        "total_parcelas": len(alvos),
        "total_vendas": len(vendas),
        "valor_total": valor_total,
        "empresas_afetadas": len(empresas),
        "venc_min": vencs[0] if vencs else None,
        "venc_max": vencs[-1] if vencs else None,
        "bloqueadas": (sum(1 for a in alvos if _bloqueada(a, bloqueios))
                       if bloqueios is not None else None),
        "por_empresa": lista_empresas,
        "preview": preview,
        "preview_truncado": len(alvos) > PREVIEW_MAX,
    }


def competencia(vencimento):
    """MM/AAAA — formato de 370.783 das 370.868 linhas de RECEBER."""
    if hasattr(vencimento, "strftime"):
        return vencimento.strftime("%m/%Y")
    iso = _iso(vencimento)
    if iso and len(iso) >= 7:
        return f"{iso[5:7]}/{iso[0:4]}"
    return "00/0000"


def gen_receber_id(conn):
    """Valor corrente de GEN_RECEBER_ID. Comparar antes/depois prova que a
    trigger atribuiu os IDs: delta == inseridos."""
    cur = conn.cursor()
    cur.execute("SELECT GEN_ID(GEN_RECEBER_ID, 0) FROM RDB$DATABASE")
    return cur.fetchone()[0]


# ID fora da lista de colunas de proposito: quem atribui e a trigger RECEBER_BI,
# via GEN_RECEBER_ID. Ver docstring do modulo.
_INSERT_SQL = """
    INSERT INTO RECEBER
        (IDVENDA, IDCLIENTE, DATA, VALORPARCELA, VALORVARIACAO, TOTALPAGO,
         PARCELA, OBS, IDVENDAFORMAPAGTO, DESCONTO, IDVENDAFORMAPAGTOPRAZO)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def inserir(conn, alvos, commit_a_cada=500, on_progress=None):
    """Grava as parcelas. Um erro derruba a linha, nao o lote — a trigger de
    bloqueio de periodo rejeita parcelas antigas individualmente e o resto do
    lote continua valido.

    Devolve {inseridos, erros, erros_detalhe, prazos_gravados}.
    """
    cur = conn.cursor()
    inseridos = 0
    erros = []
    prazos_ok = []

    for alvo in alvos:
        venc = alvo["VENCIMENTO"]
        if hasattr(venc, "strftime"):
            data_ins = venc
        else:
            data_ins = datetime.now()
        try:
            cur.execute(_INSERT_SQL, (
                alvo["IDVENDA"],
                alvo["ID_CLIENTE"],
                data_ins,
                float(alvo["VALOR_PARCELA"] or 0),
                0.0,                                        # VALORVARIACAO
                0.0,                                        # TOTALPAGO (em aberto)
                competencia(venc),
                str(alvo["OBS_DESCRICAO"] or "PARCELA")[:50],
                alvo["IDVENDAFORMAPAGTO"],
                0.0,                                        # DESCONTO
                alvo["PRAZO_ID"],
            ))
            inseridos += 1
            prazos_ok.append(alvo["PRAZO_ID"])
            if inseridos % commit_a_cada == 0:
                conn.commit()
                if on_progress:
                    on_progress(inseridos, len(alvos))
        except Exception as e:
            erros.append({
                "prazo_id": alvo["PRAZO_ID"],
                "idvenda": alvo["IDVENDA"],
                "empresa": alvo["CODIGOEMPRESA"],
                "erro": str(e)[:160],
            })

    conn.commit()
    return {
        "inseridos": inseridos,
        "erros": len(erros),
        "erros_detalhe": erros,
        "prazos_gravados": prazos_ok,
    }


def escrever_log_rollback(resultado, log_dir="."):
    """Grava o JSON que permite desfazer a execucao.

    A chave e IDVENDAFORMAPAGTOPRAZO, nao faixa de ID: e exato mesmo com escrita
    concorrente do Vulcano legado no meio da carga.
    """
    prazos = resultado.get("prazos_gravados") or []
    payload = {
        "executado_em": datetime.now().isoformat(timespec="seconds"),
        "modo": resultado.get("modo"),
        "empresa_id": resultado.get("empresa_id"),
        "inseridos": resultado.get("inseridos"),
        "erros": resultado.get("erros"),
        "erros_detalhe": (resultado.get("erros_detalhe") or [])[:50],
        "gen_receber_id_antes": resultado.get("gen_receber_id_antes"),
        "gen_receber_id_depois": resultado.get("gen_receber_id_depois"),
        "prazos_gravados": prazos,
        "rollback_sql": ("DELETE FROM RECEBER WHERE TOTALPAGO = 0 AND "
                         "IDVENDAFORMAPAGTOPRAZO IN (<prazos_gravados>)"),
    }
    try:
        os.makedirs(log_dir, exist_ok=True)
        caminho = os.path.join(
            log_dir, f"gerar_receber_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(caminho, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        return caminho
    except Exception:
        # Perder o log nao pode invalidar uma carga que ja foi commitada.
        return None


def executar(conn, modo="A", empresa_id=None, data_inicio=None, data_fim=None,
             limite=None, dry_run=True, teto=TETO_PARCELAS, log_dir=None):
    """Fluxo completo: busca -> resume -> (grava). Usado pelo CLI e pela API.

    Simulacao nunca e recusada pelo teto: e assim que o operador descobre como
    fatiar. Execucao acima do teto volta com acima_do_teto=True e inseridos=0.
    """
    modo = normalizar_modo(modo)
    bloqueios = carregar_bloqueios(conn)
    alvos = buscar_alvos(conn, modo, empresa_id, data_inicio, data_fim, limite)

    resultado = {
        "modo": modo,
        "execucao": False,
        "empresa_id": empresa_id,
        "data_inicio": data_inicio if modo == "B" else None,
        "data_fim": data_fim if modo == "B" else None,
        "limite": limite,
        "teto": teto,
        "acima_do_teto": False,
        "inseridos": 0,
        "erros": 0,
        "erros_detalhe": [],
        **resumir(alvos, bloqueios),
    }

    ignorou_datas = modo == "A" and (data_inicio or data_fim)
    nota_datas = (" Filtro de vencimento ignorado: no modo A a venda recebe a "
                  "matriz inteira de prazos." if ignorou_datas else "")

    if not alvos:
        resultado["mensagem"] = ("Nenhuma parcela a gerar para este filtro — "
                                 "o banco ja esta completo." + nota_datas)
        return resultado

    if dry_run:
        resultado["acima_do_teto"] = len(alvos) > teto
        resultado["mensagem"] = (
            f"Simulacao: {fmt_int(len(alvos))} parcelas de {fmt_int(resultado['total_vendas'])} vendas, "
            f"R$ {fmt_valor(resultado['valor_total'])}. Envie dry_run=false para gravar." + nota_datas
        )
        return resultado

    if len(alvos) > teto:
        resultado["acima_do_teto"] = True
        resultado["mensagem"] = (
            f"{fmt_int(len(alvos))} parcelas excedem o teto de {fmt_int(teto)} por execucao. "
            "Estreite o filtro: escolha uma empresa e/ou um intervalo de vencimento, "
            "ou use o campo Limite para um piloto."
        )
        return resultado

    antes = gen_receber_id(conn)
    gravacao = inserir(conn, alvos)
    depois = gen_receber_id(conn)

    resultado.update(gravacao)
    resultado["execucao"] = True
    resultado["gen_receber_id_antes"] = antes
    resultado["gen_receber_id_depois"] = depois
    resultado["mensagem"] = (
        f"{fmt_int(gravacao['inseridos'])} parcelas gravadas em RECEBER com TOTALPAGO = 0"
        + (f", {fmt_int(gravacao['erros'])} com erro." if gravacao["erros"] else ".")
        + nota_datas
    )

    if log_dir:
        resultado["log_rollback"] = escrever_log_rollback(resultado, log_dir)

    return resultado
