import json
import sys

with open(r'core/agents/tools.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_tool = '''
@tool
def calcular_custo_realizado_poc_metragem(cc_empreendimento: int, empresa_id: int = 959) -> str:
    """Ferramenta OBRIGATÓRIA para detalhar contas de Imóveis a Concluir (ex: 5639).
    Calcula a proporção IFRS 15 de cada unidade baseada na sua metragem física vs metragem total.
    Também busca o último POC registrado no Vulcano Legado e simula se o POC foi aplicado erroneamente sobre as frações.
    O retorno inclui uma matriz por APTO permitindo bater com lançamentos avulsos do Questor.
    """
    try:
        conn_v = _get_conn("vulcano")
        cur_v = conn_v.cursor()

        # Obter Empreendimento
        cur_v.execute("SELECT ID, NOME, METRAGEMTOTAL FROM EMPREENDIMENTO WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ?", (cc_empreendimento, empresa_id))
        emp = cur_v.fetchone()
        if not emp:
            return json.dumps({"status": "error", "message": f"Nenhum empreendimento vinculado ao CC {cc_empreendimento} no Firebird."})
        
        emp_id, nome_emp, metragem_total = emp[0], str(emp[1]).strip() if emp[1] else 'Desconhecido', float(emp[2] or 0)
        
        if metragem_total <= 0:
            return json.dumps({"status": "error", "message": f"A Metragem Total do Empreendimento {nome_emp} está zerada. Divisão por zero abortada."})

        # Obter Metragem de Cada Apto
        cur_v.execute("SELECT U.ID, U.DESCRICAO, U.METRAGEM FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = ?", (emp_id,))
        unidades = cur_v.fetchall()
        
        # Último POC do Vulcano Legado
        cur_v.execute("SELECT FIRST 1 PERCENTUAL, PERIODO FROM POC WHERE ID_EMPREENDIMENTO = ? ORDER BY PERIODO DESC", (emp_id,))
        poc_row = cur_v.fetchone()
        poc_percentual = float(poc_row[0]) / 100.0 if poc_row else 1.0  # Assumir 100% (1.0) se não achar
        
        conn_v.close()

        # Pegar Gasto Incorrido Total do Questor LCTOGER
        conn_q = _get_conn("questor")
        cur_q = conn_q.cursor()
        cur_q.execute("SELECT SUM(VALORLCTOGER) FROM LCTOGER WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ? AND NATUREZA = 'D'", (cc_empreendimento, empresa_id))
        row_q = cur_q.fetchone()
        gasto_incorrido_total = float(row_q[0] or 0)
        conn_q.close()

        # Calcular as proporções e teste de distorção
        matrix = []
        for u in unidades:
            uid, desc, met = u[0], str(u[1]).strip() if u[1] else str(u[0]), float(u[2] or 0)
            fracao_fisica = met / metragem_total
            
            # Custo IFRS (Equação correta: Metragem_Unid / Metragem_Total * Gasto_Incorrido_Total)
            custo_ifrs_esperado = fracao_fisica * gasto_incorrido_total
            
            # Teste de Distorção: se o sistema erradamente multiplicou a fração pelo POC
            custo_com_vicio_poc = custo_ifrs_esperado * poc_percentual

            matrix.append({
                "apto": desc,
                "metragem": met,
                "fracao_porcento": round(fracao_fisica * 100, 4),
                "custo_correto_ifrs15": round(custo_ifrs_esperado, 2),
                "teste_distorcao_com_poc": round(custo_com_vicio_poc, 2)
            })

        matrix = sorted(matrix, key=lambda x: x["apto"])
        
        return json.dumps({
            "ferramenta": "calcular_custo_realizado_poc_metragem",
            "status": "success",
            "cc_empreendimento": cc_empreendimento,
            "empreendimento": nome_emp,
            "metragem_total": metragem_total,
            "gasto_incorrido_total_lctoger": round(gasto_incorrido_total, 2),
            "poc_legado_vulcano": round(poc_percentual * 100, 2),
            "aviso": "Validação concluída. O LLM deve comparar os valores fisicos das contas 1.x com a chave 'custo_correto_ifrs15'. Se o físico coincidir sistematicamente com 'teste_distorcao_com_poc', denuncie erro IFRS 15 de mensuração de custeio retroativo atrelado erroneamente a reconhecimento POC em unidade pronta.",
            "unidades_analise": matrix[:20]  # Mandar top 20 para n sobrecarregar LLM com 8192 tokens
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Erro interno calcular_custo_realizado_poc: {e}"})

'''

if "calcular_custo_realizado_poc_metragem" not in text:
    old_list = "tools_list = ["
    new_list = "tools_list = [\n    calcular_custo_realizado_poc_metragem,"
    
    text = text + "\n\n" + new_tool
    text = text.replace(old_list, new_list)
    
    with open(r'core/agents/tools.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Tool inserida sucesso.")
else:
    print("Tool já existia.")
