import sys

with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

new_comp = '''
function TabelaMapaComparativa({ questor, vulcano1, vulcano2 }) {
  // Extract all unique units (APTOs)
  const mapAptos = {};

  const processItens = (itens, label) => {
    (itens || []).forEach(item => {
      let key = extractAptoNum(item.historico || item.descricao || '');
      if (!key) key = "SEM_UNIDADE";
      
      if (!mapAptos[key]) {
        mapAptos[key] = { questor: [], vulcano1: [], vulcano2: [], totalQuestor: 0, totalVulcano1: 0, totalVulcano2: 0 };
      }
      
      mapAptos[key][label].push(item);
      const val = item.natureza === 'D' ? Math.abs(item.valor || 0) : -Math.abs(item.valor || 0);
      mapAptos[key]["total" + label.charAt(0).toUpperCase() + label.slice(1)] += val;
    });
  };

  processItens(questor, 'questor');
  processItens(vulcano1, 'vulcano1');
  processItens(vulcano2, 'vulcano2');

  const keys = Object.keys(mapAptos).sort((a,b) => {
    if (a === "SEM_UNIDADE") return 1;
    if (b === "SEM_UNIDADE") return -1;
    // extract digits to sort numerically
    const na = parseInt(a.replace(/\D/g, '') || 0);
    const nb = parseInt(b.replace(/\D/g, '') || 0);
    return na - nb;
  });

  if (keys.length === 0) {
    return <div className="p-4 text-center text-xs text-[var(--v-text-faint)] italic">Sem dados iteráveis</div>;
  }

  return (
    <div className="flex flex-col gap-3 p-3 bg-[#0a0a0a]">
      {keys.map(k => {
        const d = mapAptos[k];
        const hasDiffVU1 = Math.abs(d.totalQuestor - d.totalVulcano1) > 0.5;
        const hasDiffVU2 = Math.abs(d.totalQuestor - d.totalVulcano2) > 0.5;
        
        return (
          <div key={k} className="bg-[var(--v-deep)] border border-[var(--v-border)] shadow-md rounded-[var(--v-radius)] overflow-hidden">
            
            {/* Cabecalho do Card */}
            <div className="flex items-center justify-between px-3 py-2 bg-[#151515] border-b border-[var(--v-border)]">
              <span className="font-black text-[12px] text-white tracking-widest uppercase">{k.replace('_', ' ')}</span>
              
              <div className="flex items-center gap-4">
                 <div className="text-[10px] font-mono">
                   <span className="text-[var(--v-text-faint)]">Questor: </span>
                   <span className={d.totalQuestor >= 0 ? "text-[var(--v-accent-3)] font-bold" : "text-[var(--v-accent)] font-bold"}>{fmt(d.totalQuestor)}</span>
                 </div>
                 <div className="text-[10px] font-mono">
                   <span className="text-[var(--v-text-faint)]">VU 2.0: </span>
                   <span className={d.totalVulcano2 >= 0 ? "text-[var(--v-accent-5)] font-bold" : "text-[var(--v-accent-2)] font-bold"}>{fmt(d.totalVulcano2)}</span>
                 </div>
                 
                 {hasDiffVU2 ? (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-widest bg-[#ff4d00]/20 text-[#ff4d00]">Divergente</span>
                 ) : (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-widest bg-[#34c759]/20 text-[#34c759]">Bateu</span>
                 )}
              </div>
            </div>

            {/* Corpo (Colunas lado a lado) */}
            <div className="grid grid-cols-3 divide-x divide-[var(--v-border)]">
              
              <div className="p-2">
                <div className="text-[9px] font-black uppercase tracking-widest text-[#34c759] mb-2 px-1 text-center">Questor ({d.questor.length})</div>
                <div className="flex flex-col gap-1">
                  {d.questor.length === 0 ? <span className="text-[#333] italic text-center text-[10px] py-1">vazio</span> : 
                   d.questor.map((x,i) => (
                    <div key={i} className="flex flex-col border border-[var(--v-border)] bg-[#111] p-1.5 rounded">
                      <div className="flex justify-between items-center mb-1">
                         <span className="text-[10px] font-mono text-white text-xs">{fmt(x.valor)} {x.natureza}</span>
                         <span className="text-[8px] text-[var(--v-text-faint)]">{x.data}</span>
                      </div>
                      <span className="text-[9px] font-mono text-[var(--v-text-muted)] truncate" title={x.historico}>{x.historico}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="p-2">
                <div className="text-[9px] font-black uppercase tracking-widest text-[#a259ff] mb-2 px-1 text-center">VU 1.0 ({d.vulcano1.length})</div>
                <div className="flex flex-col gap-1">
                  {d.vulcano1.length === 0 ? <span className="text-[#333] italic text-center text-[10px] py-1">vazio</span> : 
                   d.vulcano1.map((x,i) => (
                    <div key={i} className="flex flex-col border border-[#a259ff]/20 bg-[#111] p-1.5 rounded">
                      <div className="flex justify-between items-center mb-1">
                         <span className="text-[10px] font-mono text-white text-xs">{fmt(x.valor)} {x.natureza}</span>
                         <span className="text-[8px] text-[var(--v-text-faint)]">{x.data}</span>
                      </div>
                      <span className="text-[9px] font-mono text-[#a259ff]/70 truncate" title={x.descricao}>{x.descricao}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-2 bg-[#34c759]/5">
                <div className="text-[9px] font-black uppercase tracking-widest text-[#34c759] mb-2 px-1 text-center">VU 2.0 ({d.vulcano2.length})</div>
                <div className="flex flex-col gap-1">
                  {d.vulcano2.length === 0 ? <span className="text-[#333] italic text-center text-[10px] py-1">vazio</span> : 
                   d.vulcano2.map((x,i) => (
                    <div key={i} className="flex flex-col border border-[#34c759]/30 bg-[#34c759]/10 p-1.5 rounded">
                      <div className="flex justify-between items-center mb-1">
                         <span className="text-[10px] font-mono text-white text-xs">{fmt(x.valor)} {x.natureza}</span>
                         <span className="text-[8px] text-[#34c759]/70">{x.data}</span>
                      </div>
                      <span className="text-[9px] font-mono text-[#34c759] truncate" title={x.descricao}>{x.descricao}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        );
      })}
    </div>
  );
}
'''

replacements = {
    "function TabelaMapaAgrupada": new_comp + "\n\nfunction TabelaMapaAgrupada"
}

for k, v in replacements.items():
    content = content.replace(k, v)
    
old_mapa = '''          {aba === 'mapa' && (

            <div className="grid grid-cols-3 divide-x divide-[#111]">

              <div>

                <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)] text-center">

                  <span className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent)]">Questor Legado ({questorManual.length})</span>

                </div>

                <TabelaMapaAgrupada

                  itens={questorManual}

                  corNaturezaD="#34c759" corNaturezaC="#ff4d00"

                  titulo="Questor"

                />

              </div>

              <div>

                <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)] text-center">

                  <span className="text-[9px] font-black uppercase tracking-widest text-[#a259ff]">Vulcano 1.0 (VU) ({vulcano1.length})</span>

                </div>

                <TabelaMapaAgrupada

                  itens={vulcano1}

                  corNaturezaD="#a259ff" corNaturezaC="#ff9f0a"

                  titulo="Vulcano 1.0"

                />

              </div>

              <div>

                <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)] text-center">

                  <span className="text-[9px] font-black uppercase tracking-widest text-[#34c759]">Vulcano 2.0 (IFRS 15) ({vulcano2.length})</span>

                </div>

                <TabelaMapaAgrupada

                  itens={vulcano2}

                  corNaturezaD="#34c759" corNaturezaC="#a259ff"

                  titulo="Vulcano 2.0"

                />

              </div>

            </div>

          )}'''

new_mapa = '''          {aba === 'mapa' && (
            <TabelaMapaComparativa questor={questorManual} vulcano1={vulcano1} vulcano2={vulcano2} />
          )}'''
          
new_mapa_spaced = '\n\n'.join(new_mapa.split('\n'))
content = content.replace(old_mapa, new_mapa_spaced)

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Card view applied!")
