import firebirdsql
import traceback
import sys

def run_tests():
    print("Testing Vulcano Query...")
    try:
        conn_v = firebirdsql.connect(
            host='localhost', 
            database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB',
            port=3050,
            user='SYSDBA', 
            password='masterkey', 
            charset='WIN1252'
        )
        cur_v = conn_v.cursor()
        venda_query = """
            SELECT e.NOME, v.TOTALVENDA, v.DTOPER, v.DISTRATO, v.DATADISTRATO 
            FROM VENDA AS v 
            INNER JOIN EMPREENDIMENTO AS e ON v.IDEMPREENDIMENTO = e.ID
        """
        cur_v.execute(venda_query)
        print("VULCANO PASSED!")
    except Exception as e:
        print("VULCANO FAILED:", str(e))

    print("\nTesting Questor Query...")
    try:
        conn_q = firebirdsql.connect(
            host='localhost', 
            database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB', 
            port=3050,
            user='SYSDBA', 
            password='masterkey', 
            charset='WIN1252'
        )
        cur_q = conn_q.cursor()
        fiscal_query = """
            SELECT v.COMPRECEB, SUM(v.VLTOTREC), SUM(v.VLPIS + v.VLCOFINS)
            FROM EFDUNIDIMOBVENDIDA v
            JOIN EFDUNIDIMOBILIARIA i ON v.CODIGOEMPRESA = i.CODIGOEMPRESA AND v.CODIGOESTAB = i.CODIGOESTAB AND v.NUMCADIMOB = i.NUMCADIMOB
            GROUP BY v.COMPRECEB
        """
        cur_q.execute(fiscal_query)
        print("QUESTOR PASSED!")
    except Exception as e:
        print("QUESTOR FAILED:", str(e))

run_tests()
