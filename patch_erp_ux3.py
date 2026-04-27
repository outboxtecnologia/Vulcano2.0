"""
Patch UX3 — Reverte bloqueio do AUDITAR e filtra contasMap pelas contas dos empreendimentos
"""
path = 'frontend/src/AuditoriaERPView.jsx'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# ─── PATCH 1: Reverte botão AUDITAR — remove !filtroEmpId da condição disabled ─
OLD_BTN_DISABLED = 'disabled={loading || !periodoValido || !selectedEmpresa || !filtroEmpId}\n\n          className="ml-auto px-6 py-2.5 bg-[var(--v-accent)] text-black text-xs font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"\n          title={!filtroEmpId ? \'Selecione um empreendimento específico antes de auditar\' : \'Auditar\'}'
NEW_BTN_DISABLED = 'disabled={loading || !periodoValido || !selectedEmpresa}\n\n          className="ml-auto px-6 py-2.5 bg-[var(--v-accent)] text-black text-xs font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"'

if OLD_BTN_DISABLED in src:
    src = src.replace(OLD_BTN_DISABLED, NEW_BTN_DISABLED, 1)
    print("Patch 1 (reverte disabled AUDITAR) aplicado")
else:
    print("Patch 1 NOT FOUND")

# ─── PATCH 2: Remove banner amarelo de aviso sobre filtroEmpId ────────────────
OLD_BANNER = (
    "      {!filtroEmpId && !loading && (\n"
    "        <div className=\"flex items-center gap-3 border border-[#eab308]/30 bg-[#eab308]/8 px-4 py-2.5\" style={{ borderRadius: '2px' }}>\n"
    "          <AlertTriangle size={13} className=\"text-[#eab308] shrink-0\"/>\n"
    "          <p className=\"text-[11px] font-black uppercase tracking-widest text-[#eab308]\">\n"
    "            Selecione um empreendimento específico no filtro — auditar \"Todos\" mistura contas de diferentes obras e distorce a conciliação por conta\n"
    "          </p>\n"
    "        </div>\n"
    "      )}\n\n"
)
if OLD_BANNER in src:
    src = src.replace(OLD_BANNER, '', 1)
    print("Patch 2 (remove banner amarelo) aplicado")
else:
    print("Patch 2 NOT FOUND — tentando variação...")
    idx = src.find("!filtroEmpId && !loading")
    if idx >= 0:
        print(repr(src[idx-10:idx+400]))

# ─── PATCH 3: Adicionar derivação das contas dos empreendimentos do dashboardMeta ─
# Logo após a construção do contasMap (linha ~3967), adicionamos o filtro.
# A lógica:
#   1. Extrai do dashboardMeta todos os valores de conta configurados (conta_custo,
#      conta_estoque, conta_estconc, conta_clientes, conta_caixa, etc.)
#   2. Aplica esse Set como whitelist sobre as chaves do contasMap
# O dashboardMeta tem estrutura: { "Nome Emp": { conta_custo: 123, conta_estoque: 456, ... } }

OLD_CONTASMAP_END = (
    "    return m; // { contaId \u2192 nome }\n\n"
    "  }, [dadosPorMes]);"
)
NEW_CONTASMAP_END = (
    "    // --- Filtro por contas dos empreendimentos cadastrados ---\n"
    "    // Extrai do dashboardMeta todas as contas configuradas nos empreendimentos\n"
    "    // (conta_custo, conta_estoque, conta_estconc). Só exibe contas do universo\n"
    "    // dos empreendimentos — nunca contas genéricas avulsas do plano de contas.\n"
    "    const contasEmpreendimento = new Set();\n"
    "    Object.values(dashboardMeta || {}).forEach(emp => {\n"
    "      // Campos numéricos diretos\n"
    "      [\n"
    "        emp.conta_custo, emp.conta_estoque, emp.conta_estconc,\n"
    "        emp.conta_caixa, emp.conta_clientes, emp.conta_adi_cli,\n"
    "        emp.conta_rec, emp.conta_variacao, emp.conta_despesa,\n"
    "        emp.cc,\n"
    "      ].forEach(v => {\n"
    "        if (v) {\n"
    "          const num = parseInt(String(v).split(' ')[0], 10);\n"
    "          if (!isNaN(num) && num > 0) contasEmpreendimento.add(String(num));\n"
    "        }\n"
    "      });\n"
    "      // Campos string tipo '5639 - IMÓVEIS A CONCLUIR'\n"
    "      [emp.CONTAESTAND, emp.CONTAESTCON].forEach(v => {\n"
    "        if (v) {\n"
    "          const num = parseInt(String(v).split(' ')[0], 10);\n"
    "          if (!isNaN(num) && num > 0) contasEmpreendimento.add(String(num));\n"
    "        }\n"
    "      });\n"
    "    });\n\n"
    "    // Se encontramos contas do dashboardMeta, filtra o mapa.\n"
    "    // Se dashboardMeta ainda não foi carregado (0 contas), mostra tudo (sem filtro prematuro).\n"
    "    const filtered = contasEmpreendimento.size > 0\n"
    "      ? Object.fromEntries(Object.entries(m).filter(([cid]) => contasEmpreendimento.has(String(cid))))\n"
    "      : m;\n\n"
    "    return filtered; // { contaId \u2192 { nome, classif } }\n\n"
    "  }, [dadosPorMes, dashboardMeta]);"
)

if OLD_CONTASMAP_END in src:
    src = src.replace(OLD_CONTASMAP_END, NEW_CONTASMAP_END, 1)
    print("Patch 3 (filtro contas empreendimento) aplicado")
else:
    print("Patch 3 NOT FOUND")
    idx = src.find("return m; // { contaId")
    print(repr(src[max(0,idx-20):idx+120]))

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print("\nDONE")
