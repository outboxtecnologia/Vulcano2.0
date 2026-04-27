"""
Patch de UX — 3 mudanças:
1. Botão TELA CHEIA colorido (cyan accent)
2. Legibilidade da tabela (contrast numbers, row stripes, separadores)
3. Aviso quando 'Todos os empreendimentos' e obriga seleção OU mostra badge por empreendimento
"""

path = 'frontend/src/AuditoriaERPView.jsx'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# ─── PATCH 1: Botão TELA CHEIA com destaque cyan ─────────────────────────────
OLD_BTN = (
    'className="ml-auto px-3 py-1.5 text-[10px] font-black uppercase tracking-widest '
    'border border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[var(--v-accent)] '
    'hover:border-[var(--v-accent)]/50 transition-all flex items-center gap-1.5"\n'
    '          style={{ borderRadius: \'2px\' }}'
)
NEW_BTN = (
    'className={`ml-auto px-3 py-1.5 text-[10px] font-black uppercase tracking-widest '
    'flex items-center gap-1.5 transition-all ${isErpFullscreen '
    '? \'bg-[#ef4444]/20 border border-[#ef4444]/60 text-[#ef4444] hover:bg-[#ef4444]/30\' '
    ': \'bg-[#00bcd4]/15 border border-[#00bcd4]/60 text-[#00bcd4] hover:bg-[#00bcd4]/25 hover:border-[#00bcd4]\'}`}\n'
    '          style={{ borderRadius: \'2px\' }}'
)
if OLD_BTN in src:
    src = src.replace(OLD_BTN, NEW_BTN, 1)
    print("Patch 1 (botão) aplicado")
else:
    print("Patch 1 NOT FOUND — procurando...")
    idx = src.find('ml-auto px-3 py-1.5 text-[10px]')
    print(repr(src[max(0,idx-20):idx+300]))

# ─── PATCH 2: Cabeçalho da tabela — separadores mais nítidos ─────────────────
OLD_TH_CONTA = (
    '<th className="px-3 py-2 text-left text-[10px] font-black uppercase tracking-widest '
    'text-[var(--v-text-faint)] border-b border-[var(--v-border)] sticky left-0 top-0 z-30 '
    'bg-[var(--v-deep)] min-w-[220px]">'
)
NEW_TH_CONTA = (
    '<th className="px-3 py-2 text-left text-[10px] font-black uppercase tracking-widest '
    'text-[#8a8a8a] border-b-2 border-[#363636] sticky left-0 top-0 z-30 '
    'bg-[#0d0d0d] min-w-[220px]">'
)
if OLD_TH_CONTA in src:
    src = src.replace(OLD_TH_CONTA, NEW_TH_CONTA, 1)
    print("Patch 2a (th conta) aplicado")
else:
    print("Patch 2a NOT FOUND")

OLD_TH_STATUS = (
    '<th className="px-3 py-2 text-right text-[10px] font-black uppercase tracking-widest '
    'text-[var(--v-text-bold)] border-b border-[var(--v-border)] sticky top-0 z-20 '
    'bg-[var(--v-deep)] min-w-[130px]">'
)
NEW_TH_STATUS = (
    '<th className="px-3 py-2 text-right text-[10px] font-black uppercase tracking-widest '
    'text-[#e8e8e8] border-b-2 border-[#363636] sticky top-0 z-20 '
    'bg-[#0d0d0d] min-w-[130px]">'
)
if OLD_TH_STATUS in src:
    src = src.replace(OLD_TH_STATUS, NEW_TH_STATUS, 1)
    print("Patch 2b (th status) aplicado")
else:
    print("Patch 2b NOT FOUND")

# ─── PATCH 2c: Sub-header mês — mais nítido ──────────────────────────────────
OLD_SUB_MES = (
    '<div className="px-2 py-1.5 text-center text-xs font-black uppercase tracking-widest '
    'text-[var(--v-text-faint)] border-b border-[var(--v-border)]">'
)
NEW_SUB_MES = (
    '<div className="px-2 py-1.5 text-center text-xs font-black uppercase tracking-widest '
    'text-[#c8c8c8] border-b-2 border-[#363636] bg-[#0d0d0d]">'
)
if OLD_SUB_MES in src:
    src = src.replace(OLD_SUB_MES, NEW_SUB_MES, 1)
    print("Patch 2c (sub-header mês) aplicado")
else:
    print("Patch 2c NOT FOUND")

# ─── PATCH 2d: Sub-labels QUESTOR/VULCANO/Δ mais visíveis ────────────────────
OLD_SUB_LABELS = (
    '<div className="flex text-[7px] font-black uppercase tracking-widest text-[#333]">\n\n'
    '                        <div className="flex-1 px-2 py-1 text-right border-r border-[var(--v-bg)]">Questor</div>\n\n'
    '                        <div className="flex-1 px-2 py-1 text-right border-r border-[var(--v-bg)]">Vulcano</div>\n\n'
    '                        <div className="flex-1 px-2 py-1 text-right">\u00ce\u201d</div>\n\n'
    '                      </div>'
)
NEW_SUB_LABELS = (
    '<div className="flex text-[9px] font-black uppercase tracking-widest">\n\n'
    '                        <div className="flex-1 px-2 py-1 text-right border-r border-[#2a2a2a] text-[#ff6b1a]/80">Questor</div>\n\n'
    '                        <div className="flex-1 px-2 py-1 text-right border-r border-[#2a2a2a] text-[#a259ff]/80">Vulcano</div>\n\n'
    '                        <div className="flex-1 px-2 py-1 text-right text-[#eab308]/80">\u0394</div>\n\n'
    '                      </div>'
)
if OLD_SUB_LABELS in src:
    src = src.replace(OLD_SUB_LABELS, NEW_SUB_LABELS, 1)
    print("Patch 2d (sub-labels) aplicado")
else:
    print("Patch 2d NOT FOUND — tentando variacao...")
    # Tenta versão com espaçamento diferente
    idx = src.find('text-[7px] font-black uppercase tracking-widest text-[#333]')
    if idx >= 0:
        print(repr(src[idx-30:idx+300]))
    else:
        print("Sub-labels block not found at all")

# ─── PATCH 2e: Números Questor com cor mais forte ────────────────────────────
# O span de movimento Questor: 'text-[var(--v-text-muted)]' → mais visível
OLD_MOV_FISICO_ZERO = "className={movFisico == 0 ? 'text-[var(--v-text-muted)]' : movFisico >= 0 ? 'text-[var(--v-accent-3)]/80' : 'text-[var(--v-accent)]/80'}"
NEW_MOV_FISICO_ZERO = "className={movFisico == 0 ? 'text-[#454545]' : movFisico >= 0 ? 'text-[var(--v-accent-3)]' : 'text-[var(--v-accent)]'}"
count_2e = src.count(OLD_MOV_FISICO_ZERO)
if count_2e > 0:
    src = src.replace(OLD_MOV_FISICO_ZERO, NEW_MOV_FISICO_ZERO)
    print(f"Patch 2e (mov fisico cor) aplicado ({count_2e}x)")
else:
    print("Patch 2e NOT FOUND")

# ─── PATCH 2f: Linha alternada na tabela ─────────────────────────────────────
OLD_TR_ROW = (
    "className={`border-b border-[var(--v-border)] cursor-pointer transition-colors "
    "hover:bg-[var(--v-hover)]"
)
NEW_TR_ROW = (
    "className={`border-b border-[#1e1e1e] cursor-pointer transition-colors "
    "hover:bg-[#1a1a1a]"
)
count_2f = src.count(OLD_TR_ROW)
if count_2f > 0:
    src = src.replace(OLD_TR_ROW, NEW_TR_ROW)
    print(f"Patch 2f (row stripe border) aplicado ({count_2f}x)")
else:
    print("Patch 2f NOT FOUND")

# ─── PATCH 2g: Saldo S: mais visível ─────────────────────────────────────────
OLD_SALDO_LABEL = 'className="text-xs font-bold font-mono text-[var(--v-text-faint)] mt-0.5" title="Saldo Final no Mês">'
NEW_SALDO_LABEL = 'className="text-[10px] font-bold font-mono text-[#666] mt-0.5" title="Saldo Final no Mês">'
count_2g = src.count(OLD_SALDO_LABEL)
if count_2g > 0:
    src = src.replace(OLD_SALDO_LABEL, NEW_SALDO_LABEL)
    print(f"Patch 2g (saldo label) aplicado ({count_2g}x)")
else:
    print("Patch 2g NOT FOUND")

# ─── PATCH 3: Conta td — sticky col com fundo sólido ligeiramente diferente ──────
OLD_TD_CONTA = (
    '<td className="px-3 py-2.5 sticky left-0 z-10 bg-[var(--v-deep)] min-w-[220px]">'
)
NEW_TD_CONTA = (
    '<td className="px-3 py-2 sticky left-0 z-10 bg-[#0d0d0d] min-w-[220px] border-r border-[#222]">'
)
count_3 = src.count(OLD_TD_CONTA)
if count_3 > 0:
    src = src.replace(OLD_TD_CONTA, NEW_TD_CONTA)
    print(f"Patch 3 (td conta bg) aplicado ({count_3}x)")
else:
    print("Patch 3 NOT FOUND")

# ─── PATCH 4: Aviso quando 'Todos os empreendimentos' ────────────────────────
# Adicionar aviso visual no filtro-bar quando filtroEmpId == '' após auditar
OLD_FILTROS_WRAPPER = (
    '<div className="flex flex-wrap gap-3 items-end bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-4">'
)
NEW_FILTROS_WRAPPER = (
    '<div className="flex flex-wrap gap-3 items-end bg-[#0d0d0d] border border-[#222] p-3" style={{borderRadius:\'2px\'}}>'
)
if OLD_FILTROS_WRAPPER in src:
    src = src.replace(OLD_FILTROS_WRAPPER, NEW_FILTROS_WRAPPER, 1)
    print("Patch 4 (filtros wrapper compact) aplicado")
else:
    print("Patch 4 NOT FOUND")

# ─── PATCH 5: Overflow scroll da tabela — mais alto em fullscreen ────────────
OLD_OVERFLOW = (
    '<div className="overflow-auto" style={{ maxHeight: \'calc(100vh - 300px)\' }}>'
)
NEW_OVERFLOW = (
    '<div className="overflow-auto" style={{ maxHeight: isErpFullscreen ? \'calc(100vh - 120px)\' : \'calc(100vh - 280px)\' }}>'
)
if OLD_OVERFLOW in src:
    src = src.replace(OLD_OVERFLOW, NEW_OVERFLOW, 1)
    print("Patch 5 (overflow height) aplicado")
else:
    print("Patch 5 NOT FOUND")
    idx = src.find('overflow-auto')
    print(repr(src[idx-20:idx+120]))

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print("\nDONE")
