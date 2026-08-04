"""
popular_receber_abertas.py
==========================
OBSOLETO — NAO USE. Substituido por:

    python gerar_receber_vendas_sem_parcela.py --modo B

Dois motivos para nao rodar este arquivo:

  1. BUG: calcula o ID novo como MAX(ID)+1 e o informa no INSERT. A trigger
     RECEBER_BI so consome GEN_RECEBER_ID quando o ID vem null/0, entao o
     generator NAO avanca — e as insercoes seguintes do Vulcano legado quebram
     com violacao de PRIMARY KEY. O caminho novo omite a coluna ID.
  2. O DB_PATH abaixo esta fixo na maquina de um usuario; o motor novo le a
     conexao do .env, igual ao resto do backend.

A logica vive agora em core/services/receber_generator.py, compartilhada pelo
CLI, pelo endpoint POST /api/vulcano/gerar-parcelas e pela tela de Geracao de
Parcelas. Mantido apenas como referencia historica.

--- documentacao original ---

Popula RECEBER com as parcelas de VENDAFORMAPAGTOPRAZO que ainda nao
possuem registro correspondente em RECEBER (TOTALPAGO=0 = em aberto).

Modos:
  --dry-run   (padrao) -- apenas imprime o que seria inserido, nao grava
  --empresa X          -- filtra por CODIGOEMPRESA especifica
  --executar           -- grava de fato no banco

Regras:
  - Somente vendas sem distrato (DISTRATO <> 'S')
  - Somente formas de pagamento ativas (ATIVA = 'S')
  - Somente parcelas que NAO existem ainda em RECEBER
    (por IDVENDAFORMAPAGTOPRAZO OU por coincidencia data+valor+idvenda)
  - TOTALPAGO = 0   (em aberto)
  - VALORVARIACAO = 0
  - DESCONTO = 0
  - OBS = descricao da forma de pagamento (VENDAFORMAPAGTO.DESCRICAO)
  - PARCELA = formatado como MM/AAAA baseado em VENDAFORMAPAGTOPRAZO.DATA
  - IDs gerados a partir de MAX(ID)+1 incrementando localmente
"""
import firebirdsql
import argparse
import sys
from datetime import datetime

DB_PATH = r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB"

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true", default=True,
                    help="Apenas simula, nao insere (padrao)")
parser.add_argument("--executar", action="store_true", default=False,
                    help="Insere de fato no banco")
parser.add_argument("--empresa", type=int, default=None,
                    help="Filtrar por CODIGOEMPRESA")
parser.add_argument("--limite", type=int, default=None,
                    help="Limitar quantidade de insercoes para teste")
parser.add_argument("--data-inicio", type=str, default=None,
                    help="Inserir apenas parcelas a partir desta data (YYYY-MM-DD). Ex: 2022-01-01")
args = parser.parse_args()

dry_run = not args.executar
empresa_filtro = args.empresa
limite = args.limite
data_inicio = args.data_inicio  # ex: '2022-01-01'

print("=" * 60)
print("POPULAR RECEBER - Parcelas em Aberto")
print("=" * 60)
print(f"  Modo:      {'DRY-RUN (simulacao)' if dry_run else '*** EXECUCAO REAL ***'}")
print(f"  Empresa:   {empresa_filtro or 'TODAS'}")
print(f"  Limite:    {limite or 'sem limite'}")
print(f"  Data ini:  {data_inicio or 'sem filtro (todas as datas)'}")
print("=" * 60)

conn = firebirdsql.connect(
    host="localhost", database=DB_PATH,
    port=3050, user="SYSDBA", password="masterkey", charset="WIN1252"
)
cur = conn.cursor()

# -----------------------------------------------------------------------
# 1. Buscar proximo ID disponivel
# -----------------------------------------------------------------------
cur.execute("SELECT MAX(ID) FROM RECEBER")
max_id = cur.fetchone()[0] or 0
next_id = max_id + 1
print(f"\n  Proximo ID disponivel: {next_id}")

# -----------------------------------------------------------------------
# 2. Query: parcelas orfas (sem RECEBER) de vendas ativas sem distrato
# -----------------------------------------------------------------------
empresa_cond  = f"AND v.CODIGOEMPRESA = {empresa_filtro}" if empresa_filtro else ""
limite_cond   = f"ROWS 1 TO {limite}" if limite else ""
data_ini_cond = f"AND vpp.DATA >= '{data_inicio}'" if data_inicio else ""

query = f"""
    SELECT
        vpp.ID             AS prazo_id,
        vpp.DATA           AS vencimento,
        vpp.VALOR          AS valor_parcela,
        vpp.REFERENCIA,
        vfp.ID             AS idvendaformapagto,
        vfp.IDVENDA,
        vfp.DESCRICAO      AS obs_descricao,
        v.ID_CLIENTE,
        v.CODIGOEMPRESA
    FROM VENDAFORMAPAGTOPRAZO vpp
    JOIN VENDAFORMAPAGTO vfp ON vfp.ID = vpp.IDVENDAFORMAPAGTO
    JOIN VENDA v ON v.ID = vfp.IDVENDA
    WHERE NOT EXISTS (
        SELECT 1 FROM RECEBER r
        WHERE r.IDVENDAFORMAPAGTOPRAZO = vpp.ID
    )
    AND vfp.ATIVA = 'S'
    AND (v.DISTRATO IS NULL OR v.DISTRATO <> 'S')
    AND (vpp.VALOR_PAGO = 0 OR vpp.VALOR_PAGO IS NULL)
    {empresa_cond}
    {data_ini_cond}
    ORDER BY v.CODIGOEMPRESA, vfp.IDVENDA, vpp.DATA
    {limite_cond}
"""

cur.execute(query)
cols = [d[0] for d in cur.description]
orfas = [dict(zip(cols, row)) for row in cur.fetchall()]

print(f"\n  Parcelas orfas encontradas: {len(orfas)}")
if not orfas:
    print("  Nenhuma parcela para inserir. Banco esta completo.")
    conn.close()
    sys.exit(0)

# -----------------------------------------------------------------------
# 3. Preparar insercoes
# -----------------------------------------------------------------------
insercoes = []
for row in orfas:
    vencimento = row["VENCIMENTO"]
    if isinstance(vencimento, datetime):
        parcela_str = vencimento.strftime("%m/%Y")
        data_ins = vencimento
    else:
        parcela_str = "00/0000"
        data_ins = datetime.now()

    insercoes.append({
        "id":                    next_id,
        "idvenda":               row["IDVENDA"],
        "idcliente":             row["ID_CLIENTE"],
        "data":                  data_ins,
        "valorparcela":          row["VALOR_PARCELA"] or 0.0,
        "valorvariacao":         0.0,
        "totalpago":             0.0,
        "parcela":               parcela_str,
        "obs":                   (row["OBS_DESCRICAO"] or "PARCELA")[:50],
        "idvendaformapagto":     row["IDVENDAFORMAPAGTO"],
        "desconto":              0.0,
        "idvendaformapagtoprazo": row["PRAZO_ID"],
    })
    next_id += 1

# -----------------------------------------------------------------------
# 4. Preview
# -----------------------------------------------------------------------
print(f"\n  Primeiras 5 insercoes previstas:")
for ins in insercoes[:5]:
    print(f"    ID={ins['id']}  VENDA={ins['idvenda']}  "
          f"DATA={ins['data'].strftime('%Y-%m-%d')}  "
          f"VALOR={ins['valorparcela']}  PARCELA={ins['parcela']}  "
          f"OBS={ins['obs'][:20]}  PRAZO_ID={ins['idvendaformapagtoprazo']}")

valor_total = sum((r["valorparcela"] or 0.0) for r in insercoes)
print(f"\n  Total de registros a inserir: {len(insercoes)}")
print(f"  Soma dos valores:             R$ {valor_total:,.2f}")

# -----------------------------------------------------------------------
# 5. Executar insercoes
# -----------------------------------------------------------------------
if dry_run:
    print("\n  [DRY-RUN] Nenhuma gravacao realizada.")
    print("  Execute com --executar para gravar no banco.")
else:
    print("\n  Iniciando insercoes...")
    insert_sql = """
        INSERT INTO RECEBER
            (ID, IDVENDA, IDCLIENTE, DATA, VALORPARCELA, VALORVARIACAO,
             TOTALPAGO, PARCELA, OBS, IDVENDAFORMAPAGTO, DESCONTO,
             IDVENDAFORMAPAGTOPRAZO)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    inseridos = 0
    erros = 0
    cur2 = conn.cursor()
    for ins in insercoes:
        try:
            cur2.execute(insert_sql, (
                ins["id"],
                ins["idvenda"],
                ins["idcliente"],
                ins["data"],
                ins["valorparcela"],
                ins["valorvariacao"],
                ins["totalpago"],
                ins["parcela"],
                ins["obs"],
                ins["idvendaformapagto"],
                ins["desconto"],
                ins["idvendaformapagtoprazo"],
            ))
            inseridos += 1
            if inseridos % 100 == 0:
                conn.commit()
                print(f"    ... {inseridos} inseridos")
        except Exception as e:
            erros += 1
            print(f"    ERRO ID={ins['id']} VENDA={ins['idvenda']}: {e}")

    conn.commit()
    print(f"\n  CONCLUIDO: {inseridos} inseridos, {erros} erros.")

conn.close()
print("\nScript finalizado.")
