import main
import pprint

with open('debug_cno.md', 'w', encoding='utf-8') as f:
    conn = main.get_conn('questor')
    cur = conn.cursor()
    
    query = """
    SELECT oe.CODIGOOUTEMP, oe.NOMEOUTEMP, oe.INSCRFEDERAL, oee.INSCRFEDPRESTADORSERV
    FROM OUTRAEMPRESA oe
    JOIN OUTRAEMPEMP oee ON oe.CODIGOOUTEMP = oee.CODIGOOUTEMP
    WHERE oee.CODIGOEMPRESA = 959
    """
    cur.execute(query)
    
    f.write("# Debug OUTRAEMPRESA\n\n")
    f.write("| CODIGO | NOME | INSCRFEDERAL (oe) | INSCRFEDPRESTADORSERV (oee) |\n")
    f.write("|---|---|---|---|\n")
    for r in cur.fetchall():
        codigo = r[0]
        nome = r[1].decode('win1252', 'ignore') if isinstance(r[1], bytes) else str(r[1])
        ifederal = r[2].decode('win1252', 'ignore') if isinstance(r[2], bytes) else str(r[2])
        iprestador = r[3].decode('win1252', 'ignore') if isinstance(r[3], bytes) else str(r[3])
        
        f.write(f"| {codigo} | {nome} | {ifederal} | {iprestador} |\n")
        
    conn.close()
