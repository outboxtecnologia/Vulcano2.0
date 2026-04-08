import firebirdsql
import sys
import argparse
import datetime
import unicodedata

def limpa(v):
    if not v: return ""
    v = v.decode('win1252','ignore') if isinstance(v, bytes) else str(v)
    v = unicodedata.normalize('NFKD', v).encode('ASCII', 'ignore').decode('utf-8')
    return v.upper().strip()

def format_text(texto, tamanho):
    t = limpa(texto)
    return t.ljust(tamanho)[:tamanho]

def format_num(val, tamanho):
    if val is None: val = 0.0
    v_str = f"{abs(val):.2f}".replace('.', '')
    return v_str.zfill(tamanho)[:tamanho]

def format_doc(val, tamanho=14):
    v = limpa(val)
    v = ''.join(c for c in v if c.isdigit())
    return v.zfill(tamanho)[:tamanho]

def get_vulcano_conn():
    return firebirdsql.connect(
        host="localhost",
        database="C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB",
        port=3050,
        user="SYSDBA",
        password="masterkey",
        charset="WIN1252"
    )

def gerar_dimob(ano, cod_empresa, output_file):
    conn = get_vulcano_conn()
    cur = conn.cursor()
    
    print(f"Buscando Empresa Declaradora {cod_empresa}...")
    cur.execute("SELECT NOMEEMPRESA, CNPJ FROM EMPRESA WHERE CODIGOEMPRESA = ?", (cod_empresa,))
    emp_row = cur.fetchone()
    if not emp_row:
        print(f"Empresa {cod_empresa} não encontrada no banco Firebird!")
        return
    
    emp_nome = emp_row[0]
    emp_cnpj = emp_row[1]
    cnpj_declarante = format_doc(emp_cnpj, 14)
    print(f"Empresa: {limpa(emp_nome)} - CNPJ: {cnpj_declarante}")
    
    linhas = []
    
    # R01: Head/Identificacao Declaradora
    # A R01 da DIMOB tem tamanho variado nas especificações originais mas costuma ter pelo menos 132 a 135 bytes
    # Posicoes: 01-03: 'R01', 04-17: CNPJ, 18-21: Ano, 22: 'N' (Nao retifica), 60 carac. p/ nome...
    r01 = f"R01{cnpj_declarante}{ano:04d}N{' '*10} {' '*10}{format_text(emp_nome, 60)}"
    linhas.append(r01.ljust(130)[:130])
    
    # Puxar todas Vendas onde ocorram distratos nulos ou falsos
    query_vendas = """
    SELECT 
        V.ID, 
        V.NUMCONT, 
        V.DTOPER, 
        V.TOTALVENDA,
        C.NOME AS CLIENTE_NOME,
        C.CNPJ AS CLIENTE_DOC
    FROM VENDA V
    JOIN CLIENTE C ON V.ID_CLIENTE = C.ID
    WHERE (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
    AND V.CODIGOEMPRESA = ?
    """
    cur.execute(query_vendas, (cod_empresa,))
    vendas = cur.fetchall()
    
    seq = 1
    total_recebido = 0.0
    total_vendido = 0.0
    
    for v in vendas:
        id_venda = v[0]
        num_cont = v[1]
        dt_venda = v[2]
        val_venda = v[3] or 0.0
        c_nome = v[4]
        c_doc = v[5]
        
        # Essa venda foi assinada/firmada em 2025?
        venda_no_ano = False
        if dt_venda and hasattr(dt_venda, 'year'):
            venda_no_ano = (dt_venda.year == int(ano))
        
        # Pega recebimentos liquidados naquele ano em especifico!
        query_r = """
        SELECT SUM(TOTALPAGO) 
        FROM RECEBER 
        WHERE IDVENDA = ? 
        AND EXTRACT(YEAR FROM DATA) = ?
        """
        cur.execute(query_r, (id_venda, int(ano)))
        r_row = cur.fetchone()
        val_pago_ano = float(r_row[0]) if (r_row and r_row[0]) else 0.0
        
        # Restrição legal RFB: A DIMOB exige declaração da operação R03 EXCLUSIVAMENTE no ano de assinatura do contrato.
        if not venda_no_ano:
            continue
            
        doc_comprador = format_doc(c_doc, 14)
        nome_comprador = format_text(c_nome, 60)
        dt_venda_str = dt_venda.strftime('%d%m%Y') if dt_venda else "        "
        
        # O valor da operação é o VGV total da venda (inclusive se for a prazo)
        val_operacao = format_num(val_venda, 14)
        val_pago_fmt = format_num(val_pago_ano, 14)
        comissao = format_num(0, 14) # Zerado sem intermediação
        
        # Construindo o R03 Construção/Incorp
        r03 = (
            f"R03"
            f"{cnpj_declarante}"
            f"{ano:04d}"
            f"{seq:04d}"
            f"{doc_comprador}"
            f"{nome_comprador}"
            f"{format_text(num_cont, 20)}"
            f"{dt_venda_str}"
            f"{val_operacao}"
            f"{comissao}"
            f"{val_pago_fmt}"
        ).ljust(170)[:170]
        
        linhas.append(r03)
        seq += 1
        
        if venda_no_ano: total_vendido += val_venda
        total_recebido += val_pago_ano

    # R02 Locacoes (Alugueis) by parsing LCTOFISSAICFOP 9000200/9000201
    try:
        from injector_sped import get_db_conn
        conn_q = get_db_conn('questor')
        cur_q = conn_q.cursor()
        cur_q.execute('''
        SELECT I.DATALCTOFIS, P.NOMEPESSOA, P.INSCRFEDERAL, C.VALORCONTABILIMPOSTO, P.CODIGOPESSOA
        FROM LCTOFISSAICFOP C
        JOIN LCTOFISSAI I ON C.CODIGOEMPRESA = I.CODIGOEMPRESA AND C.CHAVELCTOFISSAI = I.CHAVELCTOFISSAI
        JOIN PESSOA P ON I.CODIGOPESSOA = P.CODIGOPESSOA
        WHERE C.CODIGOEMPRESA = ?
        AND C.CODIGOCFOP IN (9000200, 9000201)
        AND EXTRACT(YEAR FROM I.DATALCTOFIS) = ?
        ''', (cod_empresa, int(ano)))
        locacoes = cur_q.fetchall()
        for l in locacoes:
            dt_loc, c_nome, c_cpf, val, cod_pess = l
            val_loc = float(val or 0)
            if val_loc <= 0: continue
            
            doc_locador = cnpj_declarante 
            doc_locatario = format_doc(c_cpf, 14)
            nome_locatario = format_text(c_nome, 60)
            val_bruto = format_num(val_loc, 14)
            comissao = format_num(0, 14)
            ir = format_num(0, 14)
            data_str = dt_loc.strftime('%d%m%Y') if dt_loc else "        "
            contrato = format_text("NF ALUGUEL", 20)
            
            r02 = (
                f"R02"
                f"{cnpj_declarante}"
                f"{ano:04d}"
                f"{seq:04d}"
                f"{doc_locador}"
                f"{format_text(emp_nome, 60)}"
                f"{doc_locatario}"
                f"{nome_locatario}"
                f"{contrato}"
                f"{data_str}"
                f"{val_bruto}"
                f"{comissao}"
                f"{ir}"
            ).ljust(243)[:243]
            
            linhas.append(r02)
            seq += 1
            total_recebido += val_loc
    except Exception as e:
        print("Erro lendo locações Gerar:", e)

    # R09: Trailer/Fechamento (Para os somatorios da DIMOB em si - o PGD exige isso pra não corromper)
    r09 = f"R09{cnpj_declarante}{format_text(emp_nome, 60)}{format_num(total_vendido, 14)}{format_num(0, 14)}{format_num(total_recebido, 14)}"
    linhas.append(r09.ljust(120)[:120])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas))
        
    print(f"\n✅ SUCESSO! Arquivo DIMOB gerado: {output_file}")
    print(f"   => Registros R03 exportados: {seq-1}")
    print(f"   => Total de Vendas de {ano}: R$ {total_vendido:,.2f}")
    print(f"   => Retenção/Parcelas Pagas em {ano}: R$ {total_recebido:,.2f}")

def preview_dimob(ano, cod_empresa):
    conn = get_vulcano_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT NOMEEMPRESA, CNPJ FROM EMPRESA WHERE CODIGOEMPRESA = ?", (cod_empresa,))
    emp_row = cur.fetchone()
    if not emp_row:
        return {"success": False, "message": "Empresa não encontrada"}
    
    emp_nome = limpa(emp_row[0])
    
    query_vendas = """
    SELECT V.ID, V.NUMCONT, V.DTOPER, V.TOTALVENDA, C.NOME, C.CNPJ
    FROM VENDA V
    JOIN CLIENTE C ON V.ID_CLIENTE = C.ID
    WHERE (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
    AND V.CODIGOEMPRESA = ?
    """
    cur.execute(query_vendas, (cod_empresa,))
    vendas = cur.fetchall()
    
    registros = []
    total_recebido = 0.0
    total_vendido = 0.0
    
    for v in vendas:
        id_venda = v[0]
        num_cont = v[1]
        dt_venda = v[2]
        val_venda = v[3] or 0.0
        c_nome = v[4]
        c_doc = v[5]
        
        venda_no_ano = False
        if dt_venda and hasattr(dt_venda, 'year'):
            venda_no_ano = (dt_venda.year == int(ano))
            
        # Pela RFB, Incorporadoras e Loteadoras só declaram a venda 1 ÚNICA VEZ: no ano da assinatura.
        if not venda_no_ano:
            continue
        
        cur.execute("SELECT SUM(TOTALPAGO) FROM RECEBER WHERE IDVENDA = ? AND EXTRACT(YEAR FROM DATA) = ?", (id_venda, int(ano)))
        r_row = cur.fetchone()
        val_pago_ano = float(r_row[0]) if (r_row and r_row[0]) else 0.0
            
        registros.append({
            "tipo": "venda",
            "cliente_nome": limpa(c_nome),
            "cliente_cpf": format_doc(c_doc, 14),
            "unidade": limpa(num_cont),
            "valor_pago": val_pago_ano,
            "valor_venda": val_venda if venda_no_ano else 0.0
        })
        
        if venda_no_ano: total_vendido += val_venda
        total_recebido += val_pago_ano

    try:
        from injector_sped import get_db_conn
        conn_q = get_db_conn('questor')
        cur_q = conn_q.cursor()
        cur_q.execute('''
        SELECT P.NOMEPESSOA, P.INSCRFEDERAL, C.VALORCONTABILIMPOSTO, P.CODIGOPESSOA
        FROM LCTOFISSAICFOP C
        JOIN LCTOFISSAI I ON C.CODIGOEMPRESA = I.CODIGOEMPRESA AND C.CHAVELCTOFISSAI = I.CHAVELCTOFISSAI
        JOIN PESSOA P ON I.CODIGOPESSOA = P.CODIGOPESSOA
        WHERE C.CODIGOEMPRESA = ?
        AND C.CODIGOCFOP IN (9000200, 9000201)
        AND EXTRACT(YEAR FROM I.DATALCTOFIS) = ?
        ''', (cod_empresa, int(ano)))
        locacoes = cur_q.fetchall()
        for l in locacoes:
            c_nome, c_cpf, val, cod_pess = l
            val_loc = float(val or 0)
            registros.append({
                "tipo": "locacao",
                "cliente_nome": limpa(c_nome),
                "cliente_cpf": format_doc(c_cpf, 14),
                "unidade": f"Locatário #{cod_pess}",
                "valor_pago": val_loc,
                "valor_venda": 0.0
            })
            total_recebido += val_loc
    except Exception as e:
        print("Erro lendo locações Preview:", e)
        
    return {
        "success": True,
        "message": f"Pre-Auditoria Finalizada.",
        "registros": registros,
        "totais": { "vendido": total_vendido, "recebido": total_recebido }
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ano', default=2025, type=int)
    parser.add_argument('--empresa', default=959, type=int)
    args = parser.parse_args()
    
    out = f"DIMOB_{args.ano}_EMP_{args.empresa}.txt"
    try:
        gerar_dimob(args.ano, args.empresa, out)
    except Exception as e:
        print("Erro Fatal:", e)
