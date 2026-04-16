import React, { useState, useEffect } from 'react';
import SmartImporter from './SmartImporter';
import { DashboardMeta, VendasView, RecebimentosView, ConciliadorView } from './VulcanoViews';
import { EmpreendimentosView } from './EmpreendimentosView';
import { FiscalSpedView } from './FiscalSpedView';
import { TributosGlobaisView } from './TributosGlobaisView';
import { EvolucaoPOCView } from './EvolucaoPOCView';
import { SeroView } from './SeroView';
import { RawExplorerView } from './RawExplorerView';
import { CustosView } from './CustosView';
import { ContabilizacoesView } from './ContabilizacoesView';
import { AuditoriaERPView } from './AuditoriaERPView';
import { SindicatosView } from './SindicatosView';
import { JanitorView } from './JanitorView';
import './index.css';
import {
  Building2, Database, TableProperties, Fingerprint, PieChart, Construction,
  Users, Activity, ActivityIcon, BookUser, Globe2, Briefcase, Zap, Search, Bell, Download, Sun, Moon,
  RefreshCw, AlertCircle, Plus, UploadCloud, FileSpreadsheet, HandCoins,
  Terminal, ShieldCheck, ShoppingCart, DollarSign, LayoutDashboard, ShieldAlert, Landmark, Cpu, TrendingUp, Trash2
} from 'lucide-react';
import { Loader2, ArrowUpRight } from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";



  const NavItem = ({ icon, label, active, onClick }) => {
    return (
      <button 
        onClick={onClick}
        className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all duration-200 ease-in-out border-l-2 outline-none ${
          active 
            ? 'text-primary border-primary bg-surface-container-lowest font-bold shadow-[inset_4px_0_0_0_rgba(1,1,1,0)] shadow-primary/20' 
            : 'text-on-surface-variant border-transparent hover:text-on-surface hover:bg-surface-container-highest/30'
        }`}
      >
        <span className={active ? "text-primary" : "opacity-70"}>{icon}</span>
        <span className="truncate">{label}</span>
      </button>
    );
  };


export default function App() {
  const [selectedEmpresa, setSelectedEmpresa] = useState('');
  const [empresaConfirmed, setEmpresaConfirmed] = useState(false);
  const [globalEmpresas, setGlobalEmpresas] = useState([]);
  const [empresasLoading, setEmpresasLoading] = useState(true);
  const [empresasError, setEmpresasError] = useState(null);
  const [loadingSlow, setLoadingSlow] = useState(false); // true se passar de 4s
  const [manualId, setManualId] = useState('959');
  const [currentView, setCurrentView] = useState('receitas');
  const [search, setSearch] = useState('');

  const [theme, setTheme] = useState('night');
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'night') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    // Avisa o usuario se estiver lento após 4s
    const slowTimer = setTimeout(() => setLoadingSlow(true), 4000);
    fetch(`${API_BASE}/api/vulcano/empresas`)
      .then(r => r.json())
      .then(d => { setGlobalEmpresas(Array.isArray(d) ? d : (d.data || [])); setEmpresasLoading(false); setLoadingSlow(false); })
      .catch(e => {
        setEmpresasError('Erro de conexão (porta 8000). Verifique o backend ou use entrada manual.');
        setEmpresasLoading(false); setLoadingSlow(false);
      })
      .finally(() => { clearTimeout(slowTimer); });
    return () => { clearTimeout(slowTimer); };
  }, []);


  const handleRunSQL = () => alert('SQL Execution triggered for environment: ' + selectedEmpresa);

  if (!empresaConfirmed) {
    const filteredEmpresas = globalEmpresas.filter(e => 
      e.nome.toLowerCase().includes(search.toLowerCase()) || 
      e.id.toString().includes(search)
    );

    return (
      <div className="font-body overflow-hidden min-h-screen w-full relative immersive-bg" data-theme={theme} style={{ color: 'var(--v-text)' }}>
        <div className="absolute inset-0 backdrop-blur-[2px] z-0" style={{ background: 'var(--v-blur-bg)' }}></div>
        <div className="relative z-10 h-screen w-full flex flex-col items-center justify-between py-12 px-8 overflow-y-auto custom-scrollbar">
            <header className="w-full max-w-7xl flex justify-between items-center opacity-60 hover:opacity-100 transition-opacity duration-700">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-[var(--v-accent)] rounded-[var(--v-radius)] flex items-center justify-center shadow-[0_0_15px_rgba(255,77,0,0.5)]">
                  <Cpu size={18} className="text-black" />
                </div>
                <span className="font-headline text-lg font-black tracking-[0.4em] text-[var(--v-text-bold)]">VULCANO <span className="font-light opacity-50">2.0</span></span>
              </div>
              <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-muted)]">
                <span>Status: <span className="text-[var(--v-accent-3)]">Online</span></span>
                <Landmark size={14} />
              </div>
            </header>
            
            <main className="w-full max-w-6xl flex flex-col items-center gap-10 mt-12 mb-12">
               <div className="text-center space-y-4">
                   <h1 className="font-headline text-5xl md:text-6xl font-black tracking-tighter text-[var(--v-text-bold)] drop-shadow-2xl">Ecossistema de Gestão</h1>
                   <p className="font-body text-[11px] text-[var(--v-accent)] uppercase tracking-[0.6em] font-black opacity-90">Precision Audit & Financial Governance</p>
               </div>

               <div className="w-full max-w-xl relative group">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--v-text-faint)] group-focus-within:text-[var(--v-accent)] transition-colors" size={18} />
                  <input 
                    type="text"
                    placeholder="BUSCAR EMPRESA OU NODE..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full bg-black/40 backdrop-blur-md border border-white/10 rounded-[var(--v-radius)] py-4 pl-12 pr-4 text-xs font-bold uppercase tracking-widest text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50 focus:ring-1 focus:ring-[#ff4d00]/20 transition-all"
                  />
               </div>
               
               {empresasLoading ? (
                  <div className="text-[var(--v-text-bold)] flex flex-col gap-5 items-center py-16">
                    <RefreshCw className="animate-spin text-[var(--v-accent)]" size={36} />
                    <span className="text-[10px] font-black uppercase tracking-widest opacity-60">Conectando ao banco Vulcano...</span>
                    {loadingSlow && (
                      <div className="mt-4 flex flex-col items-center gap-3 bg-black/40 border border-white/10 rounded p-5">
                        <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--v-accent-6)]">Demora detectada â€” banco pode estar bloqueado</p>
                        <p className="text-[9px] text-[var(--v-text-faint)] uppercase tracking-widest">Digite o ID da empresa para entrar direto:</p>
                        <div className="flex gap-2">
                          <input value={manualId} onChange={e => setManualId(e.target.value)}
                            className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-3 py-2 text-[var(--v-text-bold)] text-xs font-mono w-24 outline-none focus:border-[#ff4d00]"
                            placeholder="959"/>
                          <button onClick={() => { setSelectedEmpresa(manualId); setEmpresaConfirmed(true); }}
                            className="px-4 py-2 bg-[var(--v-accent)] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all">
                            Entrar
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
               ) : empresasError ? (
                  <div className="flex flex-col items-center gap-4">
                    <div className="text-[var(--v-accent)] bg-[var(--v-accent)]/10 p-6 max-w-lg text-center rounded-[var(--v-radius)] font-bold border border-[#ff4d00]/30 tracking-widest uppercase text-xs shadow-2xl">
                      <AlertCircle size={28} className="mx-auto mb-3" />
                      <p className="text-[10px] leading-relaxed">{empresasError}</p>
                    </div>
                    <div className="flex flex-col items-center gap-2 bg-black/40 border border-white/10 rounded p-5">
                      <p className="text-[9px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Entrar com ID de empresa:</p>
                      <div className="flex gap-2">
                        <input value={manualId} onChange={e => setManualId(e.target.value)}
                          className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-3 py-2 text-[var(--v-text-bold)] text-xs font-mono w-24 outline-none focus:border-[#ff4d00]"
                          placeholder="959"/>
                        <button onClick={() => { setSelectedEmpresa(manualId); setEmpresaConfirmed(true); }}
                          className="px-4 py-2 bg-[var(--v-accent)] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all">
                          Entrar
                        </button>
                      </div>
                    </div>
                  </div>
               ) : filteredEmpresas.length === 0 ? (
                  <div className="text-[var(--v-text-muted)] uppercase tracking-widest text-xs border border-white/5 p-12 rounded-[var(--v-radius)] bg-black/20 backdrop-blur-sm">Nenhuma empresa localizada</div>
               ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full px-4 items-stretch pb-10">
                      {filteredEmpresas.slice(0, search ? 100 : 6).map((emp, i) => (
                          <div key={emp.id} className="group relative cursor-pointer" onClick={() => { setSelectedEmpresa(emp.id.toString()); setEmpresaConfirmed(true); }}>
                              <div className="p-8 flex flex-col h-full min-h-[220px] justify-between rounded-[var(--v-radius)] border border-white/10 hover:border-[#ff4d00]/50 bg-black/40 hover:bg-black/60 backdrop-blur-md transition-all duration-500 hover:-translate-y-2 group-hover:shadow-[0_20px_50px_rgba(255,77,0,0.15)]">
                                  <div className="space-y-6">
                                      <div className="w-12 h-12 flex items-center justify-center border border-white/10 group-hover:border-[#ff4d00]/40 group-hover:bg-[var(--v-accent)]/10 transition-all duration-500 bg-white/5 overflow-hidden relative">
                                          <div className="absolute inset-0 translate-y-full group-hover:translate-y-0 bg-[var(--v-accent)] transition-transform duration-500 opacity-20"></div>
                                          <Building2 className="text-[var(--v-text-muted)] group-hover:text-[var(--v-accent)] transition-colors z-10" size={24}/>
                                      </div>
                                      <div className="space-y-2">
                                          <h3 className="font-headline text-lg font-black tracking-widest text-[var(--v-text-bold)] group-hover:text-[var(--v-accent)] transition-colors uppercase leading-tight">{emp.nome}</h3>
                                          <div className="flex items-center gap-2">
                                            <span className="text-[10px] text-[var(--v-text-faint)] font-black px-1.5 py-0.5 border border-white/5 rounded-[var(--v-radius)]">ID {emp.id}</span>
                                            <span className="text-[9px] text-[var(--v-accent-3)] font-black uppercase tracking-widest">Ativo</span>
                                          </div>
                                      </div>
                                  </div>
                                  <div className="flex items-center justify-between mt-8">
                                      <div className="flex items-center gap-2 text-[var(--v-accent)] opacity-40 group-hover:opacity-100 transition-all duration-500">
                                          <span className="text-[10px] uppercase tracking-[0.3em] font-black">ENTRAR</span>
                                          <ArrowUpRight size={14} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                                      </div>
                                      <Fingerprint size={20} className="text-[var(--v-text-bold)]/5 group-hover:text-[var(--v-accent)]/20 transition-all duration-700" />
                                  </div>
                              </div>
                          </div>
                      ))}
                      {!search && globalEmpresas.length > 6 && (
                        <div className="col-span-1 md:col-span-2 lg:col-span-3 flex justify-center mt-6">
                           <button 
                             onClick={() => setSearch(' ')} 
                             className="text-[10px] font-black uppercase tracking-[0.4em] text-[var(--v-text-muted)] hover:text-[var(--v-text-bold)] transition-colors border-b border-white/10 hover:border-[#ff4d00] pb-1"
                           >
                              Ver todos os nodes ({globalEmpresas.length})
                           </button>
                        </div>
                      )}
                  </div>
               )}
            </main>
            
            <footer className="w-full max-w-7xl flex flex-col md:flex-row justify-between items-center gap-6 opacity-40 hover:opacity-100 transition-opacity duration-700 border-t border-white/10 pt-8 mt-auto">
              <div className="flex items-center gap-6">
                 <div className="flex items-center gap-3">
                    <span className="w-2 h-2 bg-[var(--v-accent)] rounded-[var(--v-radius)] animate-pulse shadow-[0_0_10px_#ff4d00]"></span>
                    <p className="text-[9px] font-bold text-[var(--v-text-muted)] uppercase tracking-[0.3em]">Cortex Engine Operational</p>
                 </div>
                 <div className="h-4 w-[1px] bg-white/10"></div>
                 <p className="text-[9px] font-bold text-[var(--v-text-faint)] uppercase tracking-[0.3em]">Build 2.0.4 - VULCANO LABS</p>
              </div>
              <div className="flex gap-8">
                  {['SLA', 'SYSTEM', 'PRIVACY'].map(t => (
                    <span key={t} className="text-[9px] font-black text-[var(--v-text-faint)] hover:text-[var(--v-text-muted)] cursor-pointer transition-colors uppercase tracking-[0.3em]">{t}</span>
                  ))}
              </div>
            </footer>
        </div>
      </div>
    );
  }


return (
    <div className="font-body selection:bg-[var(--v-accent)]/30 flex h-screen overflow-hidden transition-colors duration-300 immersive-bg"
         data-theme={theme}
         style={{ color: 'var(--v-text)', background: 'var(--v-deep)' }}>
        <div className="absolute inset-0 backdrop-blur-[1px] z-0"
             style={{ background: 'var(--v-blur-bg)' }}></div>

        {/* Lado Esquerdo - Stitch SideNavBar */}
        <aside className="fixed left-0 top-0 h-full w-64 z-[60] flex flex-col py-6 transition-all"
               style={{
                 background: 'var(--v-glass)',
                 backdropFilter: 'blur(24px)',
                 WebkitBackdropFilter: 'blur(24px)',
                 borderRight: '1px solid var(--v-border)'
               }}>
            <div className="px-6 mb-10 flex items-center gap-3">
                <div className="w-8 h-8 bg-[var(--v-accent)] rounded-[var(--v-radius)] flex items-center justify-center shadow-[0_0_15px_#ff4d0066]">
                  <Cpu size={18} className="text-black" />
                </div>
                <div>
                   <h1 className="font-headline font-black text-xl tracking-tighter leading-none" style={{ color: 'var(--v-text-bold)' }}>VULCANO</h1>
                   <p className="text-[9px] tracking-[0.2em] uppercase mt-1 font-black" style={{ color: 'var(--v-accent)' }}>Construction AI</p>
                </div>
            </div>
            
            <nav className="flex-1 overflow-y-auto w-full no-scrollbar px-3 space-y-8">
                <div className="space-y-1">
                    <h3 className="text-[10px] font-black opacity-60 uppercase tracking-[0.3em] pl-3 mb-3" style={{ color: 'var(--v-text-muted)' }}>Core Modules</h3>
                    <NavItem icon={<LayoutDashboard size={16}/>} label="Dashboard" active={currentView === 'receitas'} onClick={() => setCurrentView('receitas')} />
                    <NavItem icon={<Building2 size={16}/>} label="Empreendimentos" active={currentView === 'empreendimentos'} onClick={() => setCurrentView('empreendimentos')} />
                    <NavItem icon={<ShoppingCart size={16}/>} label="Vendas" active={currentView === 'vendas'} onClick={() => setCurrentView('vendas')} />
                    <NavItem icon={<DollarSign size={16}/>} label="Recebimentos" active={currentView === 'recebimentos'} onClick={() => setCurrentView('recebimentos')} />
                    <NavItem icon={<FileSpreadsheet size={16}/>} label="Smart Importer" active={currentView === 'importer'} onClick={() => setCurrentView('importer')} />
                    <NavItem icon={<UploadCloud size={16}/>} label="Conversor Universal" active={currentView === 'conciliador'} onClick={() => setCurrentView('conciliador')} />
                </div>
                <div className="space-y-1 border-t border-white/5 pt-6">
                    <h3 className="text-[10px] font-black opacity-60 uppercase tracking-[0.3em] pl-3 mb-3" style={{ color: 'var(--v-text-muted)' }}>Enterprise Suite</h3>
                    <NavItem icon={<PieChart size={16}/>} label="Tributos Globais" active={currentView === 'tributos'} onClick={() => setCurrentView('tributos')} />
                    <NavItem icon={<Construction size={16}/>} label="Evolução POC" active={currentView === 'poc'} onClick={() => setCurrentView('poc')} />
                    <NavItem icon={<ShieldCheck size={16}/>} label="Auditoria ERP" active={currentView === 'compare'} onClick={() => setCurrentView('compare')} />
                    <NavItem icon={<TrendingUp size={16}/>} label="Contabilizações" active={currentView === 'contabilizacoes'} onClick={() => setCurrentView('contabilizacoes')} />
                    <NavItem icon={<Briefcase size={16}/>} label="Fiscal & SPED" active={currentView === 'fiscal'} onClick={() => setCurrentView('fiscal')} />
                    <NavItem icon={<HandCoins size={16}/>} label="Fechamento Custos" active={currentView === 'custos'} onClick={() => setCurrentView('custos')} />
                    <NavItem icon={<Activity size={16}/>} label="Sero INSS" active={currentView === 'sero'} onClick={() => setCurrentView('sero')} />
                    <NavItem icon={<Users size={16}/>} label="Sindicatos CCT" active={currentView === 'sindicatos'} onClick={() => setCurrentView('sindicatos')} />
                    <NavItem icon={<Database size={16}/>} label="Raw Explorer" active={currentView === 'explorer'} onClick={() => setCurrentView('explorer')} />
                    <NavItem icon={<Trash2 size={16}/>} label="ðŸ§¹ Janitor SRE" active={currentView === 'janitor'} onClick={() => setCurrentView('janitor')} />
                </div>
            </nav>
            <div className="px-4 mt-auto">
                <button className="w-full bg-[var(--v-accent)] text-black py-4 rounded-[var(--v-radius)] font-black text-[10px] uppercase tracking-[0.3em] flex items-center justify-center transition-all shadow-[0_0_20px_#ff4d0033]"
                        style={{ ':hover': { background: 'var(--v-text-bold)' } }}>
                    <Plus size={14} className="mr-2" /> Nova Obra
                </button>
            </div>
        </aside>

        {/* Global Wrapper para TopNav + Content */}
        <div className="ml-64 flex-1 flex flex-col h-full bg-transparent transition-colors relative z-10 w-full overflow-hidden">

            {/* TopNavBar Stitch Design */}
            <header className="h-16 flex items-center justify-between px-8 backdrop-blur-2xl shrink-0 z-50 transition-colors"
                    style={{
                      borderBottom: '1px solid var(--v-border)',
                      background: 'var(--v-glass)'
                    }}>
                <div className="flex items-center gap-4 flex-1">
                    <div className="relative group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 transition-colors" size={16}
                                style={{ color: 'var(--v-text-faint)' }} />
                        <input
                            className="text-xs rounded-[var(--v-radius)] pl-10 pr-4 py-2 w-96 outline-none transition-all"
                            style={{
                              background: 'var(--v-card)',
                              border: '1px solid var(--v-border)',
                              color: 'var(--v-text)',
                            }}
                            placeholder="Pesquisar no Cortex Index..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>
                
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-[var(--v-radius)] shadow-sm transition-colors"
                         style={{ background: 'var(--v-card)', border: '1px solid var(--v-border)' }}>
                        <Database size={12} className="text-[var(--v-accent)] shrink-0" />
                        <select
                            value={selectedEmpresa}
                            onChange={(e) => setSelectedEmpresa(e.target.value)}
                            className="border-none outline-none text-[10px] w-52 font-black uppercase tracking-[0.2em] cursor-pointer appearance-none truncate bg-transparent"
                            style={{ color: 'var(--v-text)' }}
                        >
                            {globalEmpresas.map(emp => (
                                <option key={emp.id} value={emp.id} style={{ background: 'var(--v-card)', color: 'var(--v-text)' }}>
                                    {emp.id} - {emp.nome}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-4 h-full">
                        <div className="h-8 w-[1px] bg-white/5"></div>
                        <select value={theme} onChange={(e) => { document.documentElement.setAttribute('data-theme', e.target.value); setTheme(e.target.value); }}
                                className="px-2 py-1 outline-none font-bold text-[10px] cursor-pointer uppercase transition-all rounded-[var(--v-radius)]"
                                style={{ color: 'var(--v-text-bold)', border: '1px solid var(--v-border)', background: 'var(--v-card)' }}>
                            <option value="night">NIGHT</option>
                            <option value="light">LIGHT</option>
                            <option value="numb">NUMB</option>
                        </select>
                        <button onClick={handleRunSQL} className="hover:text-[var(--v-accent)] transition-all relative" style={{ color: 'var(--v-text-faint)' }}><Download size={18}/></button>
                        <button className="hover:text-[var(--v-accent)] transition-all relative" style={{ color: 'var(--v-text-faint)' }}>
                            <Bell size={18} />
                            <span className="absolute -top-1 -right-1 w-2 h-2 bg-[var(--v-accent)] rounded-[var(--v-radius)] shadow-[0_0_8px_#ff4d00]"></span>
                        </button>
                        <div className="h-8 w-8 rounded-[var(--v-radius)] bg-[var(--v-accent)]/10 overflow-hidden ml-2 border border-[#ff4d00]/20 p-[2px]">
                            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedEmpresa || 'Vulcano'}`} alt="User" className="w-full h-full object-cover rounded-[var(--v-radius)]" />
                        </div>
                    </div>
                </div>
            </header>


            {/* MAIN CONTENT AREA */}
            <main className="flex-1 overflow-x-hidden overflow-y-auto transition-colors p-8 relative custom-scrollbar"
                  style={{ background: 'transparent' }}>
              <div className="absolute top-0 right-0 w-[1000px] h-[1000px] rounded-[var(--v-radius)] blur-[150px] pointer-events-none -translate-y-1/2 translate-x-1/3"
                   style={{ background: 'var(--v-magma-glow)' }}></div>
              <div className="max-w-[1920px] mx-auto min-h-full flex flex-col">
                  <div className="w-full h-full">
                      {currentView === 'empreendimentos' && <EmpreendimentosView selectedEmpresa={selectedEmpresa} onNavigate={(view) => setCurrentView(view)} />}
                      {currentView === 'vendas' && <VendasView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'recebimentos' && <RecebimentosView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'receitas' && <DashboardMeta selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'conciliador' && <ConciliadorView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'importer' && <SmartImporter dbPath="poc_database.sqlite" />}
                      {currentView === 'custos' && <CustosView selectedEmpresa={selectedEmpresa} />}
                      
                      {currentView === 'fiscal' && <FiscalSpedView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'tributos' && <TributosGlobaisView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'poc' && <EvolucaoPOCView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'sero' && <SeroView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'sindicatos' && <SindicatosView />}
                      {currentView === 'explorer' && <RawExplorerView />}
                      
                      {currentView === 'compare' && <AuditoriaERPView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'contabilizacoes' && <ContabilizacoesView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'janitor' && <JanitorView />}

                      {['clientes'].includes(currentView) && (
                          <div className="h-full flex flex-col items-center justify-center py-32 text-center relative z-10 w-full animate-in zoom-in-95 duration-500">
                              <div className="w-24 h-24 mb-10 rounded-[var(--v-radius)] bg-black/40 border border-white/5 flex items-center justify-center shadow-2xl relative overflow-hidden group">
                                  <div className="absolute inset-0 bg-[var(--v-accent)] opacity-0 group-hover:opacity-10 transition-opacity"></div>
                                  <Cpu size={40} className="text-[var(--v-accent)] animate-pulse" />
                              </div>
                              <h2 className="font-headline text-4xl font-black tracking-widest text-[var(--v-text-bold)] uppercase mb-4">Módulo Offline</h2>
                              <p className="text-[var(--v-text-faint)] font-black tracking-[0.5em] uppercase text-[10px] max-w-md leading-relaxed">
                                 Aguardando integração do Cortex Node com o ERP Firebird para este dataset específico.
                              </p>
                              <div className="mt-12 flex gap-4">
                                 <button onClick={() => setCurrentView('receitas')} className="px-6 py-2 border border-white/10 text-[9px] font-black uppercase tracking-widest text-[var(--v-text-muted)] hover:border-[#ff4d00] hover:text-[var(--v-text-bold)] transition-all">Voltar ao Nexus</button>
                                 <button className="px-6 py-2 bg-[var(--v-accent)]/10 text-[var(--v-accent)] text-[9px] font-black uppercase tracking-widest border border-[#ff4d00]/20">Abrir Ticket</button>
                              </div>
                          </div>
                      )}
                  </div>
              </div>
            </main>
        </div>
    </div>
  );
}
