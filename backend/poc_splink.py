"""
POC — Splink para Reconciliacao no Conversor Universal
=======================================================
splink 4.x + DuckDB backend (embutido).
Executa probabilistic record linkage entre pagamentos PDF e contratos ERP.

Como usar:
  cd backend
  .venv\\Scripts\\python poc_splink.py
"""

import re, unicodedata, warnings
warnings.filterwarnings("ignore")

import pandas as pd
from splink import DuckDBAPI, Linker, SettingsCreator
import splink.comparison_library as cl

# ────────────────────────────────────────────────────────────────────────
# 1. DADOS DE EXEMPLO
# ────────────────────────────────────────────────────────────────────────

_pdf_rows = [
    {"uid":"P01","comprador":"JOAO CARLOS SILVA","cpf":"12345678901","unidade":"APTO 302","valor":5200.00},
    {"uid":"P02","comprador":"MARIA APARECIDA SOUZA","cpf":"98765432100","unidade":"APTO 501","valor":7800.00},
    {"uid":"P03","comprador":"JOSE PEREIRA","cpf":"11122233344","unidade":"APTO 101","valor":3100.00},
    {"uid":"P04","comprador":"ANA LUCIA FERREIRA","cpf":"","unidade":"LOJA 01","valor":9500.00},
    {"uid":"P05","comprador":"ANA L FERREIRA","cpf":"","unidade":"LOJA 01","valor":9500.00},
    {"uid":"P06","comprador":"ROBERTO ALVES SANTOS","cpf":"77788899911","unidade":"APTO 204","valor":4100.00},
    {"uid":"P07","comprador":"CARLA MENEZES","cpf":"33344455566","unidade":"APTO 307","valor":6200.00},
    {"uid":"P08","comprador":"PEDRO ALVES MONTEIRO","cpf":"44455566677","unidade":"APTO 102","valor":2800.00},
    {"uid":"P09","comprador":"LUCAS ANDRADE","cpf":"55566677788","unidade":"BLOCO B 401","valor":8800.00},
    {"uid":"P10","comprador":"FERNANDA COSTA LIMA","cpf":"66677788899","unidade":"APTO 505","valor":5500.00},
]

_erp_rows = [
    {"uid":"V01","comprador":"JOAO CARLOS DA SILVA","cpf":"12345678901","unidade":"BLOCO A APTO 302","valor":5200.00},
    {"uid":"V02","comprador":"MARIA APARECIDA SOUZA","cpf":"98765432100","unidade":"BLOCO B APTO 501","valor":7800.00},
    {"uid":"V03","comprador":"JOSE PEREIRA LOPES","cpf":"11122233344","unidade":"APTO 101","valor":3100.00},
    {"uid":"V04","comprador":"ANA LUCIA FERREIRA","cpf":"12399988877","unidade":"LOJA 01","valor":9500.00},
    {"uid":"V05","comprador":"ROBERTO ALVES SANTOS","cpf":"77788899911","unidade":"APTO 204","valor":4100.00},
    {"uid":"V06","comprador":"CARLA MENEZES ROCHA","cpf":"33344455566","unidade":"APTO 307","valor":6200.00},
    {"uid":"V07","comprador":"PEDRO MONTEIRO ALVES","cpf":"44455566677","unidade":"APTO 102","valor":2800.00},
    {"uid":"V08","comprador":"LUCAS ANDRADE JUNIOR","cpf":"55566677788","unidade":"BLOCO B APTO 401","valor":8800.00},
    {"uid":"V09","comprador":"FERNANDA COSTA LIMA","cpf":"66677788899","unidade":"APTO 505","valor":5500.00},
    {"uid":"V10","comprador":"ANA FERREIRA SANTOS","cpf":"99900011122","unidade":"LOJA 02","valor":3000.00},
]

# ────────────────────────────────────────────────────────────────────────
# 2. PRE-PROCESSAMENTO
# ────────────────────────────────────────────────────────────────────────

def norm_cpf(s):
    d = re.sub(r'\D', '', str(s or ''))
    return d if len(d) >= 11 else None

def norm_nome(s):
    s = str(s or '').upper().strip()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s)

def norm_unidade(s):
    # Remove "BLOCO X" para comparar "APTO 302" vs "BLOCO A APTO 302"
    return re.sub(r'BLOCO\s+\S+\s*', '', str(s or '').upper()).strip()

def balde_valor(v, step=500):
    try:
        return str(int(float(v or 0) / step) * step)
    except Exception:
        return "0"

def prep(rows):
    df = pd.DataFrame(rows).rename(columns={'uid': 'unique_id'})
    df['cpf_norm']    = df['cpf'].apply(norm_cpf)
    df['nome_norm']   = df['comprador'].apply(norm_nome)
    df['unid_norm']   = df['unidade'].apply(norm_unidade)
    df['valor_balde'] = df['valor'].apply(balde_valor)
    return df

df_pdf = prep(_pdf_rows)
df_erp = prep(_erp_rows)

print("=== Pagamentos PDF (normalizados) ===")
print(df_pdf[['unique_id','nome_norm','cpf_norm','unid_norm','valor_balde']].to_string(index=False))
print("\n=== Contratos ERP (normalizados) ===")
print(df_erp[['unique_id','nome_norm','cpf_norm','unid_norm','valor_balde']].to_string(index=False))

# ────────────────────────────────────────────────────────────────────────
# 3. CONFIGURACAO SPLINK
# ────────────────────────────────────────────────────────────────────────

settings = SettingsCreator(
    link_type="link_only",
    blocking_rules_to_generate_predictions=[
        "l.cpf_norm = r.cpf_norm",
        "substr(l.nome_norm,1,5) = substr(r.nome_norm,1,5)",
        "l.unid_norm = r.unid_norm",
    ],
    comparisons=[
        cl.ExactMatch("cpf_norm"),
        cl.JaroWinklerAtThresholds("nome_norm", [0.92, 0.85]),
        cl.ExactMatch("unid_norm"),
        cl.ExactMatch("valor_balde"),
    ],
    max_iterations=20,
    em_convergence=0.001,
)

db_api = DuckDBAPI()
linker = Linker([df_pdf, df_erp], settings, db_api=db_api)

# ────────────────────────────────────────────────────────────────────────
# 4. TREINAMENTO
# ────────────────────────────────────────────────────────────────────────

print("\n[1/3] Estimando u por amostragem aleatoria...")
linker.training.estimate_u_using_random_sampling(max_pairs=1e5)

print("[2/3] EM - bloqueando no CPF (pares de mesmo CPF = quase certamente matches)...")
linker.training.estimate_parameters_using_expectation_maximisation(
    "l.cpf_norm = r.cpf_norm"
)

print("[3/3] EM - bloqueando no inicio do nome...")
linker.training.estimate_parameters_using_expectation_maximisation(
    "substr(l.nome_norm,1,5) = substr(r.nome_norm,1,5)"
)

# ────────────────────────────────────────────────────────────────────────
# 5. PREDICAO
# ────────────────────────────────────────────────────────────────────────

print("\nGerando predicoes...")
df_pred = linker.inference.predict(threshold_match_probability=0.4).as_pandas_dataframe()
print(f"{len(df_pred)} par(es) candidatos acima do threshold=0.40")

# ────────────────────────────────────────────────────────────────────────
# 6. MELHOR MATCH POR PAGAMENTO
# ────────────────────────────────────────────────────────────────────────

if len(df_pred) > 0:
    matches = (
        df_pred
        .sort_values('match_probability', ascending=False)
        .drop_duplicates(subset=['unique_id_l'])   # um-para-um: melhor por PDF row
    )
    print("\n=== RESULTADO ===")
    print(f"{'ST':<4} {'PDF':<5} {'ERP':<6} {'PROB':>6}  {'NOME PDF':<28}  {'NOME ERP'}")
    print("-" * 95)
    for _, r in matches.iterrows():
        p = r['match_probability']
        st = "OK " if p >= 0.85 else "REV" if p >= 0.55 else "NO "
        nl = r.get('nome_norm_l', '?')[:26]
        nr = r.get('nome_norm_r', '?')[:26]
        print(f"[{st}] {r['unique_id_l']:<5} {r['unique_id_r']:<6} {p:>5.1%}  {nl:<28}  {nr}")
else:
    print("ATENCAO: Nenhum par gerado. Verifique as blocking rules.")

# ────────────────────────────────────────────────────────────────────────
# 7. VISUALIZACAO OPCIONAL (abre HTML no browser)
# ────────────────────────────────────────────────────────────────────────

try:
    chart = linker.visualisations.match_weights_chart()
    chart.save("splink_weights.html")
    print("\nGrafico de pesos salvo em: backend/splink_weights.html")
except Exception as e:
    print(f"\n(chart nao gerado: {e})")

# ────────────────────────────────────────────────────────────────────────
# 8. GUIA PARA INTEGRACAO EM PRODUCAO
# ────────────────────────────────────────────────────────────────────────
#
# A. SUBSTITUIR dados de exemplo por:
#    df_pdf = prep(data.extracted_data)   # JSON do endpoint /api/parser/preview-baixas
#    df_erp = prep([{                     # query Firebird VENDA JOIN CLIENTE
#        "uid": v_id, "comprador": c_nome, "cpf": c_cnpj,
#        "unidade": v_desc, "valor": valor_parcela
#    } for (v_id, c_nome, c_cnpj, v_desc, valor_parcela) in cur.fetchall()])
#
# B. COM VOLUME (centenas+ rows): o EM automatico acima funciona bem.
#    Com poucos rows: adicionar pares de treinamento supervisionados.
#
# C. THRESHOLD RECOMENDADO:
#    >= 0.85  → MATCH automatico (substituiu score >= 20 do metodo atual)
#    0.55-0.85 → mostrar como "REVISAR" no frontend (nova badge laranja)
#    < 0.55  → NAO_ENCONTRADO
#
# D. VANTAGENS vs. scoring manual:
#    * "JOAO" x "JOAO DA SILVA" → Jaro-Winkler captura sem regex custom
#    * Calibracao automatica por EM: melhora com volume
#    * Probabilidade 0-1 interpretavel, nao score arbitrario
#    * Auditavel: splink_weights.html mostra contribuicao de cada campo

print("\nPOC concluido!")
