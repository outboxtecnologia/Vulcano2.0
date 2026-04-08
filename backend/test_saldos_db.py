import firebirdsql
import json

def main():
    try:
        conn_v = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB')
        cur_v = conn_v.cursor()
        cur_v.execute("SELECT ID, NOME, CONTACLI, CONTAREC, CONTAADICLI, CONTACUSTO, CONTAESTAND FROM EMPREENDIMENTO WHERE NOME LIKE '%STUTTGART%' OR NOME LIKE '%STTUTGART%'")
        st = cur_v.fetchone()
        print('STUTTGART EMPREENDIMENTO:', st)
        if not st: return
        ccusto = st[5]

        conn_q = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
        cur_q = conn_q.cursor()

        cur_q.execute("SELECT COUNT(*) FROM LCTOCTB WHERE CODIGOEMPRESA = 959")
        print('LCTOCTB total rows:', cur_q.fetchone()[0])
        
        cur_q.execute("SELECT COUNT(*) FROM SALDOCTB WHERE CODIGOEMPRESA = 959")
        print('SALDOCTB total rows:', cur_q.fetchone()[0])

        if ccusto:
            cur_q.execute("SELECT COUNT(*) FROM LCTOCTB WHERE CODIGOEMPRESA = 959 AND (CONTACTBDEB = ? OR CONTACTBCRED = ?)", (ccusto, ccusto))
            print('LCTOCTB match for conta custo', ccusto, ':', cur_q.fetchone()[0])
            
            # test the new sql exactly
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
            print('Teste query de resultado novo (ccusto):', cur_q.fetchone())
            
    except Exception as e:
        print('ERROR:', e)

main()
