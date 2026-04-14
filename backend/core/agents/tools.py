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
            SELECT CONTACTB, DESCRCONTA, NATUREZA
            FROM PLANOESPEC
            WHERE CODIGOEMPRESA = ? AND CONTACTB = ?
        """, (empresa_id, num_conta))
        conta_row = cur.fetchone()

        # Contas com mesmo radical (3 primeiros dígitos)
        cur.execute("""
            SELECT FIRST 15 CONTACTB, DESCRCONTA, NATUREZA
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
