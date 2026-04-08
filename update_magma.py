import re

# ------------- INDEX.CSS ------------- 
magma_css = """
.immersive-bg {
    background-image: linear-gradient(to bottom, rgba(10, 10, 10, 0.4), rgba(10, 10, 10, 0.8)), url('https://lh3.googleusercontent.com/aida-public/AB6AXuBatkh8E_3pzEq9jEGasHgA7ukK09yMMyDGLVpiItN1Tb9u7FwNFdc3R7cM2wIehrHDaxH4vmdRpZXDOjwrbWmBV9X8uQg_ojutosEu-6RnqmYZ4LjcdV26vF5Dbwx-XP0gjAHdD9WjiZd0sxdZkUUvJzDGNv_GQTcAtzE1qU3HVZzvHtUN2XxIe-cKLRv4iZFS5D2YBsZuSAPtWZA41aDk5Xk9-8ypIRlZnpEpsf6kUWvTESvwH31KqZ9CVnvIwMrxiK7UAyzPBHM9');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
.ethereal-glass {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.ethereal-glass:hover {
    background: rgba(255, 86, 37, 0.05);
    border-color: rgba(255, 86, 37, 0.4);
    box-shadow: 0 0 40px rgba(255, 86, 37, 0.1);
    transform: translatey(-12px);
}
.magma-glow {
    position: absolute;
    inset: 0;
    opacity: 0;
    transition: opacity 0.6s ease;
    pointer-events: none;
    z-index: 0;
}
.group:hover .magma-glow {
    opacity: 1;
}
.text-glow {
    text-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
}
@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0px); }
}
.floating {
    animation: float 6s ease-in-out infinite;
}
"""

with open('frontend/src/index.css', 'r', encoding='utf-8') as f:
    current_css = f.read()

if '.immersive-bg' not in current_css:
    with open('frontend/src/index.css', 'a', encoding='utf-8') as f:
        f.write('\n' + magma_css)

# ------------- APP.JSX ------------- 
with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    app_code = f.read()

magma_card_code = """
const MagmaCard = ({ emp, index, onClick }) => {
  const [glowStyle, setGlowStyle] = useState({});
  const handleMouseMove = (e) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setGlowStyle({ background: `radial-gradient(circle at ${x}px ${y}px, rgba(255, 86, 37, 0.2) 0%, transparent 70%)` });
  };
  return (
      <div className="group relative floating w-full cursor-pointer z-10" style={{ animationDelay: `${index * 0.5}s` }} onMouseMove={handleMouseMove} onClick={onClick}>
          <div className="absolute inset-0 rounded-sm overflow-hidden z-0"><div className="magma-glow" style={glowStyle}></div></div>
          <div className="ethereal-glass p-10 flex flex-col h-full min-h-[300px] justify-between cursor-pointer rounded-sm relative z-10">
              <div className="space-y-6">
                  <div className="w-10 h-10 flex items-center justify-center border border-white/10 group-hover:border-primary/40 group-hover:bg-primary/10 transition-all duration-500 rounded-sm">
                      <Building2 className="text-white/40 group-hover:text-primary transition-colors" size={20}/>
                  </div>
                  <div className="space-y-3">
                      <h3 className="font-headline text-xl font-light tracking-widest text-white/80 group-hover:text-white transition-colors uppercase leading-snug">{emp.id} - {emp.nome}</h3>
                      <p className="text-white/60 text-xs leading-relaxed font-light tracking-wide opacity-60 group-hover:opacity-100 transition-opacity">ERP Analytics & Tax Governance Node.</p>
                  </div>
              </div>
              <div className="flex items-center gap-3 text-primary opacity-0 group-hover:opacity-100 transition-all duration-700 translate-y-4 group-hover:translate-y-0 mt-8">
                  <span className="text-[10px] uppercase tracking-[0.4em]">Initialize</span>
                  <ArrowUpRight size={14} className="group-hover:translate-x-1 transition-transform" />
              </div>
          </div>
      </div>
  );
};
"""

if 'const MagmaCard' not in app_code:
    app_code = app_code.replace("const App = () => {", magma_card_code + "\nconst App = () => {")

regex_empresa = re.compile(r'(if \(!empresaConfirmed\) \{.*?return \().*?(\);\s*\}\s*return \()', re.DOTALL)

new_empresa_block = """
      <div className="bg-[#0a0a0a] text-white font-body overflow-hidden min-h-screen w-full relative selection:bg-primary/30 selection:text-white flex items-center justify-center">
        {/* Immersive Background */}
        <div className="fixed inset-0 immersive-bg z-0 opacity-80"></div>
        {/* Magma Content Array */}
        <div className="relative z-10 h-screen max-h-screen w-full flex flex-col items-center justify-between py-10 px-8 overflow-y-auto no-scrollbar">
            <header className="w-full max-w-7xl flex justify-between items-center opacity-40 hover:opacity-100 transition-opacity duration-700 flex-shrink-0">
              <span className="font-headline text-lg font-light tracking-[0.6em] text-white">VULCANO</span>
              <div className="flex gap-6 text-[10px] uppercase tracking-[0.3em]">
                 <span className="cursor-pointer hover:text-primary transition-colors">Access Log</span>
                 <span className="cursor-pointer hover:text-primary transition-colors">Network</span>
              </div>
            </header>
            
            <main className="w-full max-w-6xl flex flex-col items-center gap-12 my-auto pt-8">
               <div className="text-center space-y-4">
                   <h1 className="font-headline text-5xl md:text-6xl font-extralight tracking-tight text-white/90 text-glow">
                      Select your environment
                   </h1>
                   <p className="font-body text-[10px] text-white/50 uppercase tracking-[0.5em] opacity-80">Precision Audit Ecosystem</p>
               </div>
               
               {empresasLoading ? (
                  <div className="text-white flex gap-3 items-center"><Loader2 className="animate-spin text-primary" /> Carregando matrix...</div>
               ) : empresasError ? (
                  <div className="text-error bg-error-container/10 p-6 max-w-lg text-center rounded-sm font-bold border border-error/50 tracking-widest uppercase text-xs backdrop-blur-md">{empresasError}</div>
               ) : globalEmpresas.length === 0 ? (
                  <div className="text-white/50 uppercase tracking-widest text-xs border border-white/10 p-8 rounded-sm ethereal-glass">Nenhuma empresa encontrada</div>
               ) : (
                  <div className="w-full flex md:w-full flex-col items-center gap-12 z-20">
                      
                      {/* Top Cards (Magma Nodes) */}
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 w-full px-4 items-stretch max-w-5xl mx-auto">
                           {globalEmpresas.slice(0, 3).map((emp, i) => (
                              <MagmaCard key={emp.id} emp={emp} index={i} onClick={() => { setSelectedEmpresa(emp.id.toString()); setEmpresaConfirmed(true); }} />
                           ))}
                      </div>

                      {/* Busca Integrada (Terminal Input) */}
                      <div className="w-full max-w-md mt-2 text-center px-4 ethereal-glass p-6 rounded-sm shadow-2xl relative group pb-4">
                         <div className="absolute inset-0 bg-primary/0 group-hover:bg-primary/5 transition-colors pointer-events-none rounded-sm"></div>
                         <h4 className="font-headline text-[10px] font-light uppercase tracking-[0.4em] text-white/60 mb-6 text-glow">Manual Override Access</h4>
                         <div className="flex bg-[#0a0a0a]/50 border border-white/10 rounded-sm overflow-hidden focus-within:border-primary/50 transition-colors">
                            <div className="flex items-center justify-center px-4 opacity-50">
                               <Search size={16} className="text-white group-focus-within:text-primary transition-colors" />
                            </div>
                            <input 
                               type="text"
                               list="empresas-list"
                               placeholder="Digite código matriz ou NOME..."
                               className="flex-1 bg-transparent border-none outline-none text-xs p-4 pl-0 text-white placeholder:text-white/30 font-light tracking-widest uppercase focus:ring-0 leading-none h-full"
                               onChange={(e) => {
                                 const val = e.target.value;
                                 const match = globalEmpresas.find(emp => `${emp.id} - ${emp.nome}` === val || emp.id.toString() === val);
                                 if (match) {
                                    setSelectedEmpresa(match.id.toString());
                                    setEmpresaConfirmed(true);
                                 }
                               }}
                            />
                            <datalist id="empresas-list">
                               {globalEmpresas.map(emp => (
                                 <option key={emp.id} value={`${emp.id} - ${emp.nome}`} />
                               ))}
                            </datalist>
                         </div>
                      </div>

                  </div>
               )}
            </main>
            
            <footer className="w-full max-w-7xl flex justify-between items-end opacity-40 hover:opacity-100 transition-opacity duration-700 border-t border-white/10 pt-6 flex-shrink-0">
              <div className="flex items-center gap-4">
                 <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse shadow-[0_0_10px_#ff5625]"></span>
                 <p className="text-[9px] font-body text-white/60 uppercase tracking-[0.3em]">Live Nodes Active</p>
              </div>
              <div className="flex gap-8">
                  <span className="font-headline text-[9px] uppercase tracking-[0.4em] text-white/60 hover:text-primary transition-colors cursor-pointer">Security Protocol</span>
                  <span className="font-headline text-[9px] uppercase tracking-[0.4em] text-white/60 hover:text-primary transition-colors cursor-pointer">System Archive</span>
              </div>
            </footer>
        </div>
      </div>
"""

app_code = regex_empresa.sub(r'\1' + "\n" + new_empresa_block + "\n" + r'\2', app_code)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Magma update completed!")
