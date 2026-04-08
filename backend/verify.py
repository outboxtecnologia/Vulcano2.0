import main
import pprint

with open('debug_query.txt', 'w') as f:
    conn = main.get_conn('questor')
    cur = conn.cursor()
    
    f.write("OUTRAEMPRESA E OUTRAEMPEMP\n")
    query = """
    SELECT oe.NOMEOUTEMP, oe.INSCRFEDERAL, oee.INSCRFEDPRESTADORSERV, oe.CODIGOOUTEMP
    FROM OUTRAEMPRESA oe
    JOIN OUTRAEMPEMP oee ON oe.CODIGOOUTEMP = oee.CODIGOOUTEMP
    WHERE oee.CODIGOEMPRESA = 959
    """
    cur.execute(query)
    for r in cur.fetchall():
        f.write(f"{r}\n")
    
    conn.close()
