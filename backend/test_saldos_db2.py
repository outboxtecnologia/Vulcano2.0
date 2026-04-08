import firebirdsql
import json

def main():
    try:
        conn_v = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB')
        cur_v = conn_v.cursor()
        cur_v.execute("SELECT ID, NOME, CONTACLI, CONTAREC, CONTAADICLI, CONTACUSTO, CONTAESTAND FROM EMPREENDIMENTO WHERE NOME LIKE '%STUTTGART%' OR NOME LIKE '%STTUTGART%'")
        st = cur_v.fetchone()
        
        output = ''
        output += f'STUTTGART: {st}\n'
        ccusto = st[5]

        conn_q = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
        cur_q = conn_q.cursor()
        
        if ccusto:
            data_fim = '2025-12-31'
            cur_q.execute("""
                SELECT 
                    SUM(CASE WHEN CONTACTBDEB = ? THEN VALORLCTOCTB ELSE 0 END) as V_DEB,
                    SUM(CASE WHEN CONTACTBCRED = ? THEN VALORLCTOCTB ELSE 0 END) as V_CRED
                FROM LCTOCTB 
                WHERE CODIGOEMPRESA = 959 
                  AND (CONTACTBDEB = ? OR CONTACTBCRED = ?) 
                  AND (CHAVEORIGEM NOT STARTING WITH 'ZZ') 
                  AND DATALCTOCTB <= ?
            """, (ccusto, ccusto, ccusto, ccusto, data_fim))
            row = cur_q.fetchone()
            output += f'RESULTADO PARA CONTA CUSTO {ccusto}: {row}\n'
            
        open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_saldos_out.txt', 'w', encoding='utf-8').write(output)
            
    except Exception as e:
        open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_saldos_out.txt', 'w', encoding='utf-8').write('ERROR: ' + str(e))

if __name__ == '__main__':
    main()
