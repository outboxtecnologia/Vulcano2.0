import os
import sys
import asyncio

# Garante path correto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn
from vector_engine import init_db, generate_embeddings_batch, save_embeddings

async def processar_lote(lote_raw, fonte):
    """
    Recebe dicionários com {'id', 'empresa_id', 'ano_mes', 'texto_original', 'meta'}
    Converte para embedding e salva.
    """
    textos = [f"{r['texto_original']} [VALOR R$ {r['meta_dados'].get('valor', 0)}]" for r in lote_raw]
    
    # Chama Vertex Em Lotes de 100/250 para evitar erro 400
    matrizes = []
    chunk_size = 100
    for i in range(0, len(textos), chunk_size):
        chunk = textos[i:i+chunk_size]
        print(f"[{fonte}] Gerando Embeddings {i} a {i+len(chunk)}...")
        m = await generate_embeddings_batch(chunk)
        matrizes.extend(m)
        
    # Anexa as matrizes aos payloads
    for i, r in enumerate(lote_raw):
        r["embedding"] = matrizes[i]
        
    save_embeddings(lote_raw)
    print(f"[{fonte}] Lote salvo com sucesso no banco (Total: {len(lote_raw)})")


async def sync_questor_amostra(empresa_id: int):
    print("\n--- Iniciando Extração Questor ---")
    cq = get_conn('questor')
    cur = cq.cursor()
    cur.execute("""
        SELECT C.CHAVELCTOCTB, C.DATALCTOCTB, C.VALORLCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, 
           '' as desc,
           C.CODIGOORIGLCTOCTB,
           H.DESCRHISTCTB
    FROM LCTOCTB C
    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
    WHERE C.CODIGOEMPRESA = ?
          AND EXTRACT(YEAR FROM C.DATALCTOCTB) = 2025
          AND EXTRACT(MONTH FROM C.DATALCTOCTB) IN (5, 6)
          AND C.CODIGOORIGLCTOCTB <> 'ZZ'
    """, (empresa_id,))
    
    lote = []
    for r in cur.fetchall():
        chave = r[0]
        dt = r[1].strftime('%Y-%m') if r[1] else "2025-00"
        valor = float(r[2] or 0.0)
        deb = int(r[3] or 0)
        cred = int(r[4] or 0)
        desc_padrao = str(r[7] or "").strip() if len(r) > 7 else ""
        texto_limpo = f"{desc_padrao}".strip().upper()
        if not texto_limpo:
            texto_limpo = "LANCAMENTO SEM DESCRICAO"
            
        lote.append({
            "id": f"Q_{chave}",
            "fonte": "QUESTOR",
            "empresa_id": empresa_id,
            "ano_mes": dt,
            "texto_original": texto_limpo,
            "meta_dados": {
                "valor": valor,
                "deb": deb,
                "cred": cred,
                "chave": chave
            }
        })
    
    if lote:
        await processar_lote(lote, "QUESTOR")

async def sync_vulcano_amostra(empresa_id: int):
    print("\n--- Iniciando Extração Vulcano ---")
    cv = get_conn('vulcano')
    cur = cv.cursor()
    
    cur.execute("""
        SELECT R.ID, R.DATA, R.TOTALPAGO, V.DESCUNIDIMOB, V.IDEMPREENDIMENTO, E.CODIGOHISTRECEBIMENTO
        FROM RECEBER R
        JOIN VENDA V ON V.ID = R.IDVENDA
        JOIN EMPREENDIMENTO E ON E.ID = V.IDEMPREENDIMENTO
        WHERE E.CODIGOEMPRESA = ?
          AND EXTRACT(YEAR FROM R.DATA) = 2025
          AND EXTRACT(MONTH FROM R.DATA) IN (5, 6)
          AND R.TOTALPAGO > 0
    """, (empresa_id,))
    
        # Fetch Questor standard texts for mapping
    try:
        cq = get_conn('questor')
        cur_q = cq.cursor()
        cur_q.execute("SELECT CODIGOHISTCTB, DESCRHISTCTB FROM HISTORICOCTB")
        hist_questor = {int(r[0]): str(r[1] or "") for r in cur_q.fetchall() if r[0]}
        cq.close()
    except Exception:
        hist_questor = {}

    lote = []
    for r in cur.fetchall():
        r_id = r[0]
        dt = r[1].strftime('%Y-%m') if r[1] else "2025-00"
        valor = float(r[2] or 0.0)
        unid = _s_decode(r[3])
        hist_code = int(r[5] or 0) if len(r) > 5 else 0
        hist_str = hist_questor.get(hist_code, "RECEBIMENTO PARCELA")
        
        # O Vulcano gera históricos lógicos depois, mas na base de recebimentos o marcador é a unidade.
        # Nós encriamos um texto que reflete o mesmo que aparece no dashboard
        texto_limpo = f"{hist_str} UNID {unid}".upper()
        
        lote.append({
            "id": f"V_REC_{r_id}",
            "fonte": "VULCANO",
            "empresa_id": empresa_id,
            "ano_mes": dt,
            "texto_original": texto_limpo,
            "meta_dados": {
                "valor": valor,
                "unidade": unid
            }
        })
        
    if lote:
        await processar_lote(lote, "VULCANO")

async def run_sync_all():
    print("Testando Inicialização e Conexão PGVector...")
    try:
        init_db()
        print("Tabelas garantidas.")
    except Exception as e:
        print(f"Erro Fatal conectando ao PostgreSQL. Ele está vivo?\n{e}")
        return

    empresa = 959
    await sync_questor_amostra(empresa)
    await sync_vulcano_amostra(empresa)
    print("Sincronização Vectorial PoC Completa.")

if __name__ == "__main__":
    asyncio.run(run_sync_all())
