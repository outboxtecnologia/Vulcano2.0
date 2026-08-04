"""
gerar_receber_vendas_sem_parcela.py
===================================
CLI de geracao de parcelas em RECEBER. A logica vive em
core/services/receber_generator.py, compartilhada com o endpoint
POST /api/vulcano/gerar-parcelas e com a tela "Geracao de Parcelas".

Modos:
  A (padrao)  venda sem NENHUMA parcela em RECEBER -> gera a matriz inteira dela.
              Venda que ja tem qualquer parcela nao e tocada.
  B           parcelas orfas (prazo sem linha em RECEBER), inclusive de vendas ja
              parcialmente lancadas. B contem A.

Uso:
  python gerar_receber_vendas_sem_parcela.py                        # dry-run, modo A
  python gerar_receber_vendas_sem_parcela.py --modo B
  python gerar_receber_vendas_sem_parcela.py --empresa 95 --executar
  python gerar_receber_vendas_sem_parcela.py --modo B --data-inicio 2025-01-01 --executar

Cuidado com --limite no modo A: ele corta a venda no meio, e a venda passa a
"ter parcela" — some da fila e nunca recebe o resto. Para piloto use --empresa.

O teto de TETO_PARCELAS por execucao vale aqui tambem; --forcar ignora (o CLI e
operado por quem tem acesso ao servidor; a tela nao tem esse escape).

Rollback: --executar grava um JSON com os IDVENDAFORMAPAGTOPRAZO inseridos.
  DELETE FROM RECEBER WHERE TOTALPAGO = 0 AND IDVENDAFORMAPAGTOPRAZO IN (...)
"""
import argparse
import os
import sys

import firebirdsql

from core.services.receber_generator import (TETO_PARCELAS, executar, fmt_int,
                                             fmt_valor)

parser = argparse.ArgumentParser()
parser.add_argument("--modo", choices=["A", "B", "a", "b"], default="A",
                    help="A = venda sem nenhuma parcela (padrao); B = parcelas orfas")
parser.add_argument("--executar", action="store_true", help="Grava de fato (padrao: dry-run)")
parser.add_argument("--empresa", type=int, default=None, help="Filtrar por CODIGOEMPRESA")
parser.add_argument("--data-inicio", default=None, help="Vencimento >= YYYY-MM-DD (so modo B)")
parser.add_argument("--data-fim", default=None, help="Vencimento <= YYYY-MM-DD (so modo B)")
parser.add_argument("--limite", type=int, default=None, help="FIRST N (piloto)")
parser.add_argument("--forcar", action="store_true", help="Ignora o teto de linhas por execucao")
parser.add_argument("--log-dir", default=".", help="Onde gravar o JSON de rollback")
args = parser.parse_args()

modo = args.modo.upper()
dry_run = not args.executar

print("=" * 72)
print("GERAR PARCELAS EM RECEBER")
print("=" * 72)
print(f"  Modo:     {modo} — " + ("venda sem nenhuma parcela" if modo == "A" else "parcelas orfas"))
print(f"  Execucao: {'DRY-RUN (simulacao)' if dry_run else '*** GRAVACAO REAL ***'}")
print(f"  Empresa:  {args.empresa or 'TODAS'}")
if modo == "B":
    print(f"  Periodo:  {args.data_inicio or 'sem inicio'} .. {args.data_fim or 'sem fim'}")
print(f"  Limite:   {args.limite or 'sem limite'}")
print(f"  Teto:     {'IGNORADO (--forcar)' if args.forcar else fmt_int(TETO_PARCELAS)}")
print("=" * 72)

conn = firebirdsql.connect(
    host=os.environ["FIREBIRD_HOST_VULCANO"],
    database=os.environ["DB_PATH_VULCANO"],
    port=int(os.environ.get("FIREBIRD_PORT", "3050")),
    user=os.environ["FIREBIRD_USER"],
    password=os.environ["FIREBIRD_PASSWORD"],
    charset="WIN1252",
)

try:
    r = executar(
        conn,
        modo=modo,
        empresa_id=args.empresa,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
        limite=args.limite,
        dry_run=dry_run,
        teto=float("inf") if args.forcar else TETO_PARCELAS,
        log_dir=args.log_dir if not dry_run else None,
    )
finally:
    conn.close()

print(f"\n  Vendas alvo:      {fmt_int(r['total_vendas']):>12}")
print(f"  Parcelas:         {fmt_int(r['total_parcelas']):>12}")
print(f"  Valor total:      R$ {fmt_valor(r['valor_total']):>12}")
print(f"  Empresas:         {fmt_int(r['empresas_afetadas']):>12}")
if r["venc_min"]:
    print(f"  Vencimentos:      {r['venc_min']} .. {r['venc_max']}")
if r.get("bloqueadas"):
    print(f"  Em periodo bloqueado (vao falhar): {fmt_int(r['bloqueadas'])}")

if r["preview"]:
    print("\n  Amostra:")
    for p in r["preview"][:5]:
        print(f"    venda={p['idvenda']:<7} emp={p['empresa']:<6} venc={p['data']}  "
              f"valor={fmt_valor(p['valor']):>14}  {p['obs'][:28]}")

if r["por_empresa"] and len(r["por_empresa"]) > 1:
    print(f"\n  Por empresa ({len(r['por_empresa'])}):")
    print(f"    {'EMP':>6} {'VENDAS':>7} {'PARCELAS':>9} {'VALOR':>18}")
    for e in r["por_empresa"][:20]:
        print(f"    {e['empresa']:>6} {e['vendas']:>7} {e['parcelas']:>9}   R$ {fmt_valor(e['valor']):>14}")
    if len(r["por_empresa"]) > 20:
        print(f"    ... e mais {len(r['por_empresa']) - 20} empresas")

print(f"\n  {r['mensagem']}")

if r["execucao"]:
    print(f"\n  Inseridos: {fmt_int(r['inseridos'])}   Erros: {fmt_int(r['erros'])}")
    delta = r["gen_receber_id_depois"] - r["gen_receber_id_antes"]
    print(f"  GEN_RECEBER_ID: {r['gen_receber_id_antes']} -> {r['gen_receber_id_depois']} (delta {delta})")
    if delta != r["inseridos"]:
        print("  ATENCAO: delta do generator != inseridos. A trigger RECEBER_BI"
              " pode nao ter atribuido os IDs — verifique antes de seguir.")
    for e in r["erros_detalhe"][:5]:
        print(f"    erro prazo={e['prazo_id']} venda={e['idvenda']}: {e['erro']}")
    if r.get("log_rollback"):
        print(f"  Log de rollback: {r['log_rollback']}")

sys.exit(1 if r.get("acima_do_teto") else 0)
