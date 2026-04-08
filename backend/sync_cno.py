import main
import difflib

def sync_cno():
    conn_vulcano = main.get_conn("vulcano")
    cur_v = conn_vulcano.cursor()
    
    # Limpa strings literais "None" que podem ter sido salvas
    cur_v.execute("UPDATE EMPREENDIMENTO SET CNO = NULL WHERE CNO = 'None'")
    conn_vulcano.commit()
    
    cur_v.execute("SELECT ID, NOME, CNO FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = 959")
    
    empreendimentos = []
    for r in cur_v.fetchall():
        emp_id = r[0]
        nome = r[1].decode('win1252', 'ignore') if isinstance(r[1], bytes) else str(r[1])
        cno_atual = r[2].decode('win1252', 'ignore') if isinstance(r[2], bytes) else (str(r[2]) if r[2] else None)
        empreendimentos.append({
            "id": emp_id,
            "nome": nome.strip(),
            "cno_atual": cno_atual
        })
    print(f"Lendo Vulcano: {len(empreendimentos)} obras.")
    
    try:
        conn_questor = main.get_conn("questor")
        cur_q = conn_questor.cursor()
        
        # O CNO está de fato em INSCRFEDERAL de OUTRAEMPRESA (Ex: 90.000.638.747-7)
        # INSCRFEDPRESTADORSERV tem o CNPJ da construtora. 
        # Vamos pegar da INSCRFEDERAL (r[1]).
        query = """
        SELECT oe.NOMEOUTEMP, oe.INSCRFEDERAL 
        FROM OUTRAEMPRESA oe
        JOIN OUTRAEMPEMP oee ON oe.CODIGOOUTEMP = oee.CODIGOOUTEMP
        WHERE oee.CODIGOEMPRESA = 959
        """
        cur_q.execute(query)
            
        outraemp_data = []
        for r in cur_q.fetchall():
            n = r[0].decode('win1252', 'ignore') if isinstance(r[0], bytes) else str(r[0])
            cno = r[1].decode('win1252', 'ignore') if isinstance(r[1], bytes) else str(r[1])
            if cno and cno.strip() and cno.strip() != 'None' and n and n.strip():
                # Foca em pegar só os que parecem CNO (ex: com 45. ou 90. ou 12 dígitos) se possível
                # Mas vamos colocar de forma crua aqui:
                outraemp_data.append({"nome": n.strip().upper(), "cno": cno.strip()})
                
        print(f"Lendo Questor: {len(outraemp_data)} CNOs disponiveis.")
        conn_questor.close()
    except Exception as eq:
        print("Erro ao acessar Questor:", eq)
        conn_vulcano.close()
        return

    sucessos = 0
    for emp in empreendimentos:
        target_name = emp["nome"].upper()
        
        nomes_questor = [o["nome"] for o in outraemp_data]
        matches = difflib.get_close_matches(target_name, nomes_questor, n=1, cutoff=0.45)
        
        if matches:
            best_match_name = matches[0]
            cno_encontrado = next(o["cno"] for o in outraemp_data if o["nome"] == best_match_name)
            
            print(f"✅ Match: '{emp['nome']}' -> Questor: '{best_match_name}' | CNO: {cno_encontrado}")
            cur_v.execute("UPDATE EMPREENDIMENTO SET CNO = ? WHERE ID = ?", (cno_encontrado, emp["id"]))
            sucessos += 1
        else:
            print(f"❌ Sem match: '{emp['nome']}'")

    if sucessos > 0:
        conn_vulcano.commit()
        print(f"SUCESSO! {sucessos} CNOs atualizados no banco do Vulcano.")
    else:
        print("Nenhum CNO foi alterado.")
        
    conn_vulcano.close()

if __name__ == "__main__":
    sync_cno()
