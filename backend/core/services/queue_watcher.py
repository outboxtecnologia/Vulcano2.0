import os
import asyncio
import hashlib
import json
import io
import pdfplumber
import traceback

FILA_ROOT = os.environ.get("FILA_PDFS_PATH", r"C:\Vulcano2.0\Fila_PDFs")

async def process_new_file(filepath, folder_type, db_conn, gemini_async_func):
    queue_id = None
    try:
        with open(filepath, "rb") as f:
            content = f.read()
            
        file_hash = hashlib.sha256(content).hexdigest()
        filename = os.path.basename(filepath)
        file_type = "pdf" if filename.lower().endswith(".pdf") else "xlsx" if "xls" in filename.lower() else "csv"
        target_table = "RECEBIMENTOS" if folder_type.lower() == "recebimentos" else "VENDAS"

        cur = db_conn.cursor()
        cur.execute("SELECT id FROM smart_importer_queue WHERE file_hash = ?", (file_hash,))
        if cur.fetchone():
            return # Arquivo já foi processado (Deduplicação por Hash)

        cur.execute("""
            INSERT INTO smart_importer_queue (filename, file_hash, file_type, target_table, status)
            VALUES (?, ?, ?, ?, ?)
        """, (filename, file_hash, file_type, target_table, "PROCESSANDO"))
        queue_id = cur.lastrowid
        db_conn.commit()

        extracted_text = ""
        if file_type == "pdf":
            def _extract():
                res = []
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    for page in pdf.pages[:20]: # Limite seguro para não estourar RAM
                        text = page.extract_text()
                        if text:
                            res.append(text)
                return "\n".join(res)
            extracted_text = await asyncio.to_thread(_extract)
        
        schema = '{"empresa_cnpj": "", "tabela": [{"data": "", "valor": "", "descricao": "", "documento": ""}]}'
        prompt = f"""Extraia todas as informações de faturamento/recebimento/venda presentes no documento e estruture-as como uma Tabela (array de objetos).
Importante: descubra e retorne o CNPJ da empresa dona do documento em 'empresa_cnpj'.
A 'tabela' deve ser um array onde cada objeto representa uma linha financeira (ex: um recebimento ou um contrato). Extraia o máximo de colunas/chaves possíveis baseadas no contexto (ex: cliente, cpf, vencimento, pagamento, multa, juros).
Retorne APENAS um JSON no formato indicado:
{schema}

Texto do Documento:
{extracted_text[:15000]}"""

        result = await gemini_async_func(prompt)
        
        cnpj_detectado = result.get("empresa_cnpj", "")
        tabela = result.get("tabela", [])

        cur.execute("""
            UPDATE smart_importer_queue
            SET status = 'AGUARDANDO_REVISAO',
                cnpj_detectado = ?,
                extracted_json = ?
            WHERE id = ?
        """, (cnpj_detectado, json.dumps(tabela), queue_id))
        db_conn.commit()

    except Exception as e:
        print(f"Erro ao processar {filepath}: {e}")
        traceback.print_exc()
        if queue_id:
            cur = db_conn.cursor()
            cur.execute("UPDATE smart_importer_queue SET status = 'ERRO' WHERE id = ?", (queue_id,))
            db_conn.commit()

async def watch_folders(db_conn, gemini_async_func):
    folders = ["Recebimentos", "Vendas"]
    for f in folders:
        path = os.path.join(FILA_ROOT, f)
        os.makedirs(path, exist_ok=True)
        
    processed_files = set()
    
    while True:
        try:
            for f in folders:
                folder_path = os.path.join(FILA_ROOT, f)
                for filename in os.listdir(folder_path):
                    if filename.startswith("."): continue
                    filepath = os.path.join(folder_path, filename)
                    if not os.path.isfile(filepath): continue
                    
                    if filepath not in processed_files:
                        processed_files.add(filepath)
                        await process_new_file(filepath, f, db_conn, gemini_async_func)
        except Exception as e:
            print(f"Erro no loop do Watcher: {e}")
            
        await asyncio.sleep(5) # Polling a cada 5 segundos

def start_queue_watcher(db_conn, gemini_async_func):
    print(f"Iniciando Watcher do Smart Importer na pasta {FILA_ROOT}...")
    asyncio.create_task(watch_folders(db_conn, gemini_async_func))
