with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''           )}

        </div>

      </div>,

      document.body'''

good = '''           )}

        </div>
        
        {/* POPUP DE DETALHES DA UNIDADE */}
        {detalheModal && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/90 p-4 animate-in fade-in">
            <div className="bg-[#111] border border-[#ffcc00]/30 rounded-xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
              <div className="flex items-center justify-between px-5 py-4 border-b border-[#222] bg-[#1a1a1a]">
                <div className="flex flex-col">
                   <h3 className="text-[#ffcc00] font-black uppercase tracking-widest text-sm flex items-center gap-2">Extrato de Créditos — Razão 5639</h3>
                   <p className="text-xs text-gray-400 font-mono mt-1">Unidade {detalheModal.unidade} • Lote: {detalheModal.periodo}</p>
                </div>
                <button onClick={() => setDetalheModal(null)} className="text-gray-400 hover:text-white bg-[#222] hover:bg-red-500/20 px-3 py-1 rounded transition-colors text-xs uppercase font-bold">FECHAR</button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-5">
                {detalheModal.dados.length === 0 ? (
                  <p className="text-gray-500 text-sm font-mono text-center py-10">Nenhum espelho textual de apropriação detectado neste período.</p>
                ) : (
                  <div className="flex flex-col gap-3">
                     {detalheModal.dados.map((d, i) => (
                       <div key={i} className="bg-[#1a1a1a] p-4 rounded-lg border border-[#333] hover:border-blue-500/50 transition-colors">
                          <div className="flex justify-between items-start mb-2 border-b border-[#222] pb-2">
                             <span className="text-blue-400 font-mono font-bold text-sm">R$ {d.valor.toLocaleString('pt-BR', {minimumFractionDigits:2})}</span>
                             <span className="text-[10px] text-gray-500 uppercase tracking-widest">{d.ano}-{str(d.mes).padStart(2, '0')}</span>
                          </div>
                          <p className="text-xs font-mono text-gray-300 whitespace-pre-wrap">{d.str}</p>
                       </div>
                     ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

      </div>,

      document.body'''

text = text.replace(bad, good)

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

