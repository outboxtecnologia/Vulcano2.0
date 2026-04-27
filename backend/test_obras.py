from main import get_sero_obras
r = get_sero_obras(959)
print(f"Total obras com dados: {len(r)}")
for o in r:
    folha = "F" if o["tem_folha"] else " "
    gps   = "G" if o["tem_gps"]   else " "
    nome  = o["nome"][:40]
    inscr = o["inscricao"]
    oid   = o["id"]
    print(f"  [{folha}{gps}] OUTEMP={oid:6} | {nome:40} | {inscr}")
