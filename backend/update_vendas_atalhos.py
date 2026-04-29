import re

with open("frontend/src/VulcanoViews.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# Trocar os atalhos para bater com o design (Enter, ⌘L, ⇧⌘R, ⇧⌘E, ⇧⌘D)
content = content.replace('Ver Condições (Fluxo)', 'Abrir estrutura financeira')
content = content.replace('HL</span>', 'Enter</span>')

content = content.replace('Registrar Recebimento Manual', 'Lançar parcela manual')
content = content.replace('HR</span>', '⌘L</span>')

content = content.replace('HD</span>', '⇧⌘D</span>')

# Adicionar exportar pdf
export_btn = """
                            <button className="flex justify-between items-center bg-[#222] hover:bg-[#333] border border-[#333] p-3 rounded-lg text-[11px] font-bold text-white transition-colors group">
                                <span className="flex items-center gap-2"><FileText size={14} className="text-[#888] group-hover:text-white"/> Exportar contrato (.pdf)</span>
                                <span className="text-[9px] text-[#666] font-mono bg-[#111] px-1.5 py-0.5 rounded border border-[#333]">⇧⌘E</span>
                            </button>
                            <button className="flex justify-between items-center bg-[#222] hover:bg-[#333] border border-[#333] p-3 rounded-lg text-[11px] font-bold text-white transition-colors group">
                                <span className="flex items-center gap-2"><RefreshCw size={14} className="text-[#888] group-hover:text-white"/> Reconciliar com Questor</span>
                                <span className="text-[9px] text-[#666] font-mono bg-[#111] px-1.5 py-0.5 rounded border border-[#333]">⇧⌘R</span>
                            </button>"""

content = content.replace(
    '⌘L</span>\n                            </button>',
    '⌘L</span>\n                            </button>' + export_btn
)

# Adicionar a Bottom Status Bar no VendasView
status_bar = """
      <div className="bg-[#1A1A1A] border-t border-[#333] px-6 py-3 flex justify-between items-center shrink-0 z-20">
        <div className="flex gap-4 text-[10px] uppercase font-bold tracking-widest text-[#666]">
            <span>↑ ↓ NAVEGAR</span>
            <span>↵ AÇÃO</span>
            <span>/ BUSCAR</span>
            <span>⌘K COMANDOS</span>
            <span>⇧⌘N NOVA VENDA</span>
        </div>
        <div className="text-[10px] uppercase font-bold tracking-[0.2em] text-[#888]">
            EXIBINDO {filtered.length} · TOTAL {formatCurrency(totalGeral)}
        </div>
      </div>
"""

# Inserir a status_bar logo antes do Modal de Nova Venda
content = content.replace(
    '{/* MODAL NOVA VENDA (Apenas Form Antigo Simplificado) */}',
    status_bar + '\n      {/* MODAL NOVA VENDA (Apenas Form Antigo Simplificado) */}'
)

with open("frontend/src/VulcanoViews.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("VendasView atalhos updated")
