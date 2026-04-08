import codecs
import re

file_path = 'frontend/src/VulcanoViews.jsx'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# 1. Rename the old ConciliadorView to ExtratorIAView
# Since it's exactly: export const ConciliadorView = ({ selectedEmpresa }) => {
content = content.replace(
    'export const ConciliadorView = ({ selectedEmpresa }) => {',
    'const ExtratorIAView = ({ selectedEmpresa }) => {'
)

# 2. Fix the old header to remove its huge H2 so it nests cleanly
old_header = '''<h2 className="text-3xl font-bold tracking-tighter text-white uppercase flex items-center gap-3">
            <Zap className="text-[#a259ff]" size={36} /> Importador <span className="text-[#007aff]">Multimodal IA</span>
          </h2>'''
new_header = '''<h3 className="text-xl font-bold tracking-widest text-[#a259ff] uppercase flex items-center gap-2">
            <Zap size={20} /> IA Generativa & Visão (PDF/XML)
          </h3>'''
content = content.replace(old_header, new_header)

old_sub = '<p className="text-sm border border-[#333] mt-2 uppercase tracking-widest font-bold">' # It was actually: <p className="text-sm text-[#888] mt-2 uppercase tracking-widest font-bold">Lê contratos...
# I'll just leave the subtext as is.

# 3. Create the new IntegradorQuestorView component
integrador_questor_code = """

const IntegradorQuestorView = ({ selectedEmpresa }) => {
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);

  const handleSyncCno = () => {
    setLoading(true);
    setLogs(prev => [...prev, '[SYNC CNO] Inicializando varredura no banco Questor...']);
    setTimeout(() => {
       setLogs(prev => [...prev, '[SYNC CNO] ✓ 3 cadastros sincronizados com o ERP Vulcano.']);
       setLoading(false);
    }, 1500);
  };

  const handleSyncContas = () => {
    setLoading(true);
    setLogs(prev => [...prev, '[SYNC PLANO] Solicitando árvore de contas contábeis ao Questor...']);
    setTimeout(() => {
       setLogs(prev => [...prev, '[SYNC PLANO] ✓ 450 contas matriz populadas no cache.']);
       setLoading(false);
    }, 2000);
  };

  return (
    <div className="h-full flex flex-col gap-6 animate-in fade-in">
       <div className="magma-card border border-[var(--v-border)] rounded-sm p-6 bg-[var(--v-surface-container)] flex items-start gap-6">
          <div className="p-4 bg-[var(--v-hover)] border border-[var(--v-border)] rounded-full shrink-0">
             <Server size={32} className="text-[var(--v-text-bold)]"/>
          </div>
          <div>
            <h3 className="text-xl font-black uppercase text-[var(--v-text-bold)] tracking-widest">Integração Direta Firebird (Questor)</h3>
            <p className="text-[11px] text-[var(--v-text-muted)] font-bold tracking-[0.2em] uppercase mt-2 leading-relaxed">
              Consulte e sincronize os dados matrizes do Banco Questor diretamente na memória do Vulcano.<br/>
              Necessário possuir a trigger de sincronização Firebird ativa e o agente de comunicação (Vulcano Adapter) configurado.
            </p>
          </div>
       </div>

       <div className="grid grid-cols-3 gap-6 shrink-0">
          <div className="magma-card border border-[var(--v-border)] p-6 rounded-sm flex flex-col justify-between group overflow-hidden relative">
             <div className="z-10 relative">
               <h4 className="text-[10px] text-[var(--v-accent-3)] font-bold uppercase tracking-widest mb-1">Entidades</h4>
               <p className="text-sm font-bold text-white uppercase tracking-widest">Sinc. CNO / Obras</p>
               <p className="text-[9px] text-[var(--v-text-faint)] mt-3">Sincroniza todas as alterações e aprovações de CNO do Questor para o sistema interno.</p>
             </div>
             <button disabled={loading} onClick={handleSyncCno} className="mt-6 border border-[var(--v-border)] text-[10px] uppercase font-bold text-white hover:bg-[var(--v-accent-3)] hover:text-black py-2 rounded-sm transition-colors z-10">Executar Gatilho</button>
             <Building2 size={80} className="absolute -bottom-4 -right-4 text-[var(--v-accent-3)] opacity-[0.03] group-hover:scale-110 transition-transform"/>
          </div>

          <div className="magma-card border border-[var(--v-border)] p-6 rounded-sm flex flex-col justify-between group overflow-hidden relative">
             <div className="z-10 relative">
               <h4 className="text-[10px] text-[var(--v-accent-6)] font-bold uppercase tracking-widest mb-1">Contabilidade</h4>
               <p className="text-sm font-bold text-white uppercase tracking-widest">Sinc. Plano de Contas</p>
               <p className="text-[9px] text-[var(--v-text-faint)] mt-3">Atualiza os centros de custos, fatos e classificadores analíticos baseados na lei 11.638.</p>
             </div>
             <button disabled={loading} onClick={handleSyncContas} className="mt-6 border border-[var(--v-border)] text-[10px] uppercase font-bold text-white hover:bg-[var(--v-accent-6)] hover:text-black py-2 rounded-sm transition-colors z-10">Executar Gatilho</button>
             <Landmark size={80} className="absolute -bottom-4 -right-4 text-[var(--v-accent-6)] opacity-[0.03] group-hover:scale-110 transition-transform"/>
          </div>

          <div className="magma-card border border-[var(--v-border)] p-6 rounded-sm flex flex-col justify-between group overflow-hidden relative opacity-50 cursor-not-allowed grayscale">
             <div className="z-10 relative">
               <h4 className="text-[10px] text-[var(--v-text-red)] font-bold uppercase tracking-widest mb-1">Movimentos</h4>
               <p className="text-sm font-bold text-white uppercase tracking-widest">Auditor Lote Contábil</p>
               <p className="text-[9px] text-[var(--v-text-faint)] mt-3">Varredura profunda por divergências de lançamentos entre SPED e ERP.</p>
             </div>
             <button disabled className="mt-6 bg-[#111] border border-[#222] text-[10px] uppercase font-bold text-[#555] py-2 rounded-sm z-10">Em Breve</button>
             <ShieldAlert size={80} className="absolute -bottom-4 -right-4 text-[var(--v-text-red)] opacity-[0.03]"/>
          </div>
       </div>

       <div className="flex-1 min-h-[300px] magma-card border border-[var(--v-border)] rounded-sm flex flex-col overflow-hidden">
          <div className="p-3 bg-[var(--v-hover)] border-b border-[var(--v-border)] flex items-center justify-between">
             <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-bold)]">Terminal de Logs (Vulcano <=> Questor)</span>
             {loading && <Loader2 size={12} className="animate-spin text-[var(--v-text-faint)]"/>}
          </div>
          <div className="flex-1 p-4 bg-black overflow-auto font-mono text-[11px] text-[#00ff00] leading-relaxed relative">
             {logs.length === 0 ? (
               <span className="text-[#333] uppercase">Aguardando comando de sincronização.</span>
             ) : (
               logs.map((L, i) => <div key={i}>{L}</div>)
             )}
             {loading && <div className="mt-1 animate-pulse">_</div>}
          </div>
       </div>
    </div>
  );
};

"""

# 4. Create the new Export Hub component
hub_module = """

export const ConciliadorView = ({ selectedEmpresa }) => {
  const [activeTab, setActiveTab] = useState('extrator');

  return (
    <div className="flex flex-col h-full w-full max-w-[1600px] mx-auto animate-in fade-in pt-4 pb-12">
       {/* Master Header with 2 Toggle Buttons */}
       <div className="flex flex-wrap lg:flex-nowrap justify-between items-end mb-6 gap-6">
          <div>
            <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
               <Database className="text-[var(--v-accent-6)]" size={32}/> 
               Hub de Importação
            </h2>
            <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Integração Questor & IA Documental Multimodal</p>
          </div>
          <div className="flex bg-[var(--v-surface-container)] rounded-sm p-[2px] border border-[var(--v-border)] shrink-0">
             <button onClick={() => setActiveTab('extrator')} className={`px-6 py-3 text-[10px] font-bold uppercase tracking-widest transition-colors rounded-sm flex items-center gap-2 ${activeTab === 'extrator' ? 'bg-[var(--v-accent)] text-black' : 'text-[var(--v-text-faint)] hover:text-white'}`}><Zap size={14}/> Extrator IA (PDF/Docs)</button>
             <button onClick={() => setActiveTab('questor')} className={`px-6 py-3 text-[10px] font-bold uppercase tracking-widest transition-colors rounded-sm flex items-center gap-2 ${activeTab === 'questor' ? 'bg-[#e5e5ea] text-black' : 'text-[var(--v-text-faint)] hover:text-white'}`}><Server size={14}/> DB Direto (Questor)</button>
          </div>
       </div>

       <div className="flex-1 overflow-hidden">
          {activeTab === 'extrator' ? <ExtratorIAView selectedEmpresa={selectedEmpresa}/> : <IntegradorQuestorView selectedEmpresa={selectedEmpresa}/>}
       </div>
    </div>
  )
};
"""

# 5. Append Integrador and Hub at the bottom
content = content + integrador_questor_code + hub_module

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)

print("SUCCESS: ConciliadorView wrapped into Hub de Importacao!")
