"""
Serviço de Povoamento ERP (Questor)
Responsável por formatar, validar e persistir as partidas contábeis mapeadas
pelo motor Vulcano no banco de dados físico da contabilidade (LCTOCTB).
Garante idempotência (purge & replace) baseado na tag VU.
"""
import uuid
import collections
from datetime import datetime
from main import get_conn

def inject_batch_to_questor(empresa_id: int, target_ym: str, virtual_entries: list):
    """
    Injeta um lote de lançamentos contábeis no Questor, substituindo lançamentos
    anteriores da mesma origem (VU) para o mesmo período e empresa,
    prevenindo duplicação.
    
    target_ym: 'YYYY-MM'
    virtual_entries: Lista de dicts {conta: int, mov: float, nat: 'D'|'C', hist: str}
    """
    if not virtual_entries:
        return {"success": True, "inserted": 0, "message": "Nenhum lançamento a injetar."}
        
    conn_q = get_conn("questor")
    cur_q = conn_q.cursor()
    
    # 1. Configura data do final do mês do target_ym
    import calendar
    y, m = map(int, target_ym.split("-"))
    last_day = calendar.monthrange(y, m)[1]
    data_fim_mes = f"{y:04d}-{m:02d}-{last_day:02d}"
    
    try:
        # A. Idempotência: Deletar lançamentos antigos da origem VU para esta Empresa e Competência
        # Importante: Como LCTOCTB em Questor pode ter várias restrições, se houver tabelas filhas pode dar erro.
        # Estamos assumindo que os lançamentos VU são independentes e leaf nodes.
        cur_q.execute("""
            DELETE FROM LCTOCTB 
            WHERE CODIGOEMPRESA = ? 
              AND EXTRACT(YEAR FROM DATALCTOCTB) = ?
              AND EXTRACT(MONTH FROM DATALCTOCTB) = ?
              AND CODIGOORIGLCTOCTB = 'VU'
        """, [empresa_id, y, m])
        deleted_count = cur_q.rowcount

        # Postgres: o Questor-PG tem trigger BEFORE INSERT (lctoctbbichavef) que atribui
        # CHAVELCTOCTB via SEQUENCE POR EMPRESA quando o valor vem NULL. NUNCA informar a
        # chave manualmente aqui: um MAX(CHAVELCTOCTB) GLOBAL faria o trigger avançar a
        # sequence da empresa em loop (nextval) até alcançar o valor global -> trava.
        _pg = getattr(conn_q, "kind", "firebird") == "postgres"

        # B. Encontrar o último CHAVELCTOCTB para simular SEQUENCE (só no Firebird).
        if _pg:
            max_chave = 0  # não usado: o trigger gera a chave
        else:
            cur_q.execute("SELECT MAX(CHAVELCTOCTB) FROM LCTOCTB")
            max_chave = cur_q.fetchone()[0] or 0

        # C. Encontrar o último CODIGOLCTOPROG para simular SEQUENCE (Lançamento Programado Genérico)
        cur_q.execute("SELECT MAX(CODIGOLCTOPROG) FROM LCTOCTB")
        max_prog = cur_q.fetchone()[0] or 0
        
        # O histórico contábil genérico que usaremos (ID 99)
        cod_hist = 99
        origem_dado = 1 # 1=Digitado, 2=Importado etc
        
        # D. Preparar e agrupar lançamentos para inserção
        # A requisição "vários para vários" aprova o uso de single-sided entries no Questor.
        # Ou seja: Injetamos 1 linha física de LCTOCTB para CADA perna Débito ou Crédito, 
        # com a contra-partida NULL, agrupados sob a mesma origrm/lote lógico.
        
        inserts = []
        for idx, entry in enumerate(virtual_entries):
            # entry structure: {"conta": 5665, "mov": 150.0, "nat": "C", "historico": "Receita ..."}
            is_deb = str(entry.get('nat', '')).upper() == 'D'
            
            conta_deb = entry.get('conta') if is_deb else None
            conta_cred = None if is_deb else entry.get('conta')
            valor = float(entry.get('mov', 0.0))
            hist = str(entry.get('historico', 'Injeção VU'))[:250]
            
            # Geração de ID primário: no PG deixa NULL (trigger por-empresa atribui);
            # no Firebird mantém o MAX+idx+1 histórico.
            current_chave = None if _pg else (max_chave + idx + 1)

            inserts.append((
                empresa_id,
                max_prog,
                current_chave,
                data_fim_mes,
                valor,
                'VU',                 # CODIGOORIGLCTOCTB isolando nosso bloco
                conta_deb,            # CONTACTBDEB (pode ser null)
                conta_cred,           # CONTACTBCRED (pode ser null)
                cod_hist,             # CODIGOHISTCTB padrao 99
                hist,                 # COMPLHIST
                origem_dado           # ORIGEMDADO
            ))
            
        if inserts:
            cur_q.executemany("""
                INSERT INTO LCTOCTB (
                    CODIGOEMPRESA, CODIGOLCTOPROG, CHAVELCTOCTB, DATALCTOCTB,
                    VALORLCTOCTB, CODIGOORIGLCTOCTB, CONTACTBDEB, CONTACTBCRED,
                    CODIGOHISTCTB, COMPLHIST, ORIGEMDADO
                ) VALUES (?, ?, ?, CAST(? AS DATE), ?, ?, ?, ?, ?, ?, ?)
            """, inserts)
            
        conn_q.commit()
        
        return {
            "success": True, 
            "deleted_previous": deleted_count,
            "inserted": len(inserts),
            "message": f"Integrado com sucesso. {len(inserts)} partidas injetadas no ERP (vários-para-vários)."
        }
    except Exception as e:
        conn_q.rollback()
        import traceback
        traceback.print_exc()
        raise Exception(f"Erro ao injetar matriz VU na Questor: {str(e)}")
