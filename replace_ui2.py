import re

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'\{\/\* Par lado a lado \*\/\}[\s\S]*?<\/div>\s*<\/div>'

replacement = """{/* Par lado a lado */}
                  <div className="grid grid-cols-2 gap-2 text-[10px] mb-2">
                    <div className="bg-[#0a0a0a] border border-[#ff4d00]/15 rounded p-2 flex flex-col gap-1 max-h-[140px] overflow-y-auto">
                      <p className="text-[8px] font-black uppercase tracking-widest text-[#ff4d00] ml-1">Questor</p>
                      {(m.questor_detalhe && m.questor_detalhe.length > 0 ? m.questor_detalhe : [m.questor]).map((q, idx) => (
                          <div key={idx} className="bg-[#111] p-1.5 rounded border border-[#ff4d00]/10">
                            <p className="font-mono font-bold text-[#666] text-[8px]">{q.data} | c/{q.conta}</p>
                            <p className="font-bold text-[#aaa] truncate" title={q.historico || q.chave}>{(q.historico || q.chave || '?').slice(0,50)}</p>
                            <p className="font-black text-[#34c759] mt-0.5">{fmt(q.valor)} <span className="text-[#444]">{q.natureza}</span></p>
                          </div>
                      ))}
                    </div>
                    <div className="bg-[#0a0a0a] border border-[#a259ff]/15 rounded p-2 flex flex-col gap-1 max-h-[140px] overflow-y-auto">
                      <p className="text-[8px] font-black uppercase tracking-widest text-[#a259ff] ml-1">Vulcano</p>
                      {(m.vulcano_detalhe && m.vulcano_detalhe.length > 0 ? m.vulcano_detalhe : [m.vulcano]).map((v, idx) => (
                          <div key={idx} className="bg-[#111] p-1.5 rounded border border-[#a259ff]/10">
                            <p className="font-mono font-bold text-[#666] text-[8px]">{v.data} | c/{v.conta}</p>
                            <p className="font-bold text-[#aaa] truncate" title={v.historico || v.logica}>{(v.historico || v.logica || '?').slice(0,50)}</p>
                            <p className="font-black text-[#a259ff] mt-0.5">{fmt(v.valor)} <span className="text-[#444]">{v.natureza}</span></p>
                          </div>
                      ))}
                    </div>
                  </div>"""

text, count = re.subn(pattern, replacement, text)
print(f'Replaced {count} occurrences')

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
