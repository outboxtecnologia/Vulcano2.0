import re

path = 'frontend/src/AuditoriaERPView.jsx'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# ─── PATCH 1: Adicionar createPortal no import do react-dom ───────────────────
if "createPortal" not in src:
    src = src.replace(
        "import { createPortal } from 'react-dom';",
        "import { createPortal } from 'react-dom';"
    )
    # Se não existir, adicionar após o import do react
    if "createPortal" not in src:
        src = src.replace(
            "import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';",
            "import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';\nimport { createPortal } from 'react-dom';"
        )

print("createPortal import:", "createPortal" in src)

# ─── PATCH 2: Estado fullscreen e conversão do return em erpContent ───────────
OLD_TEMTE = "  const temDados = Object.keys(dadosPorMes).length > 0;\n\n  const [isErpFullscreen, setIsErpFullscreen] = useState(false);\n\n  const erpContent = ("
if OLD_TEMTE in src:
    print("Patch 2 ja aplicado — skip")
else:
    OLD2 = "  const temDados = Object.keys(dadosPorMes).length > 0;\n\n\n\n  return (\n\n    <div className=\"flex flex-col gap-5 pb-10 text-[var(--v-text)] animate-in fade-in\">"
    if OLD2 not in src:
        # Tenta sem \r
        OLD2 = src[src.find("const temDados"):src.find("const temDados")+400]
        print("DEBUG temDados block:", repr(OLD2[:200]))
    else:
        NEW2 = """  const temDados = Object.keys(dadosPorMes).length > 0;

  const [isErpFullscreen, setIsErpFullscreen] = useState(false);

  const erpContent = (
    <div className={`text-[var(--v-text)] ${isErpFullscreen ? 'flex flex-col' : 'flex flex-col gap-5 pb-10 animate-in fade-in'}`}>"""
        src = src.replace(OLD2, NEW2, 1)
        print("Patch 2 aplicado")

# ─── PATCH 3: Header compacto com toggle fullscreen ───────────────────────────
HEADER_OLD = '      {/* Header — NÃO sticky, rola com o conteúdo. Compacta em fullscreen */}'
if HEADER_OLD not in src:
    print("Patch 3: header comment not found, skipping (may already be applied)")
else:
    # Encontrar e substituir o bloco do header
    header_start = src.find(HEADER_OLD)
    # Encontrar o '{/* Filtros */}' que vem depois
    filtros_marker = src.find('{/* Filtros */}', header_start)
    if filtros_marker < 0:
        print("Patch 3: filtros marker not found")
    else:
        old_header_block = src[header_start:filtros_marker]
        new_header_block = """      <div className={`flex items-center gap-3 border-b border-[var(--v-border)] ${isErpFullscreen ? 'px-5 py-2 bg-[#0d0d0d] sticky top-0 z-50' : 'pb-3 pt-1'}`}>
        <ShieldCheck className="text-[var(--v-accent)] shrink-0" size={isErpFullscreen ? 16 : 22}/>
        <div className="flex flex-col leading-none gap-0.5">
          <h2 className={`font-black tracking-tighter text-[var(--v-text-bold)] leading-none ${isErpFullscreen ? 'text-sm' : 'text-xl'}`}>
            Auditoria ERP
          </h2>
          {!isErpFullscreen && (
            <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-faint)] font-black">
              Calculado (Vulcano) \u00d7 Registrado (Questor)
            </p>
          )}
        </div>
        <button
          onClick={() => setIsErpFullscreen(f => !f)}
          title={isErpFullscreen ? 'Sair do modo tela cheia (Esc)' : 'Expandir \u2014 sobrepoe sidebar e header para trabalho intensivo'}
          className="ml-auto px-3 py-1.5 text-[10px] font-black uppercase tracking-widest border border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[var(--v-accent)] hover:border-[var(--v-accent)]/50 transition-all flex items-center gap-1.5"
          style={{ borderRadius: '2px' }}
        >
          {isErpFullscreen ? '\u2715 SAIR' : '\u26f6 TELA CHEIA'}
        </button>
      </div>

      """
        src = src.replace(old_header_block, new_header_block, 1)
        print("Patch 3 aplicado")

# ─── PATCH 4: Coluna conta compacta (max-w reduzido + classif em tooltip) ─────
OLD_CONTA = '            <span className="text-[12px] font-bold text-[var(--v-text-faint)] truncate" title={contaNome}>{contaNome}</span>'
if OLD_CONTA not in src:
    print("Patch 4: conta nome span not found")
else:
    # Extrair classif e nome do contaNome (formato: "1.1.02.0001 - BANCO X" ou "BANCO X")
    NEW_CONTA = """            <span className="font-mono text-[10px] text-[var(--v-text-faint)] shrink-0 tracking-tight"
              title={contaNome}>
              {(() => {
                const parts = contaNome ? contaNome.split(' - ') : [];
                if (parts.length >= 2) {
                  return <><span className="text-[var(--v-text-dim)]">{parts[0]}</span><span className="text-[var(--v-text-faint)] ml-1 truncate max-w-[150px] inline-block align-bottom">{parts.slice(1).join(' - ')}</span></>;
                }
                return <span className="truncate max-w-[170px] inline-block align-bottom">{contaNome}</span>;
              })()}
            </span>"""
    src = src.replace(OLD_CONTA, NEW_CONTA, 1)
    print("Patch 4 aplicado")

# ─── PATCH 5: Fechar com portal fullscreen ────────────────────────────────────
# Substituir o return final
OLD_RETURN_FINAL = "    </div>\n\n  );\n\n};"
if OLD_RETURN_FINAL in src:
    # Pega a última ocorrência (fim do componente AuditoriaERPView)
    last_idx = src.rfind(OLD_RETURN_FINAL)
    if last_idx > 4000:  # garante que é o do componente principal
        NEW_RETURN = """    </div>
  );

  if (isErpFullscreen) {
    return createPortal(
      <div
        style={{
          position: 'fixed', inset: 0, zIndex: 9000,
          background: 'var(--v-deep)', display: 'flex',
          flexDirection: 'column', overflow: 'hidden',
        }}
        onKeyDown={e => { if (e.key === 'Escape') setIsErpFullscreen(false); }}
        tabIndex={-1}
      >
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px 40px' }} className="custom-scrollbar">
          {erpContent}
        </div>
      </div>,
      document.body
    );
  }

  return erpContent;

};"""
        src = src[:last_idx] + NEW_RETURN + src[last_idx+len(OLD_RETURN_FINAL):]
        print("Patch 5 aplicado")
    else:
        print("Patch 5: last_idx too small:", last_idx)
else:
    print("Patch 5: return final not found, checking...")
    print(repr(src[-300:]))

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE")
