import React, { useState, useEffect } from 'react';
import { 
  Database, Table2, Layers, Search, Code, Key, Download, Loader2, PieChart,
  LayoutDashboard, Construction, ShieldAlert, BrainCircuit, Bell, Settings, ArrowUpRight,
  Building2, Users, ShoppingCart, DollarSign, FileUp, Zap
} from 'lucide-react';
import './index.css';
import { EmpreendimentosView, ClientesView, VendasView, RecebimentosView, ConciliadorView } from './VulcanoViews';
import SmartImporter from './SmartImporter';

const App = () => {
  const [currentView, setCurrentView] = useState('receitas'); // 'explorer', 'receitas', 'poc', 'compare', 'llama_painel'

  const [tables, setTables] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedTable, setSelectedTable] = useState(null);
  const [tableData, setTableData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDb, setSelectedDb] = useState('questor');

  // Global Vulcano State
  const [globalEmpresas, setGlobalEmpresas] = useState([]);
  const [selectedEmpresa, setSelectedEmpresa] = useState('');

  // Receitas State
  const [receitasData, setReceitasData] = useState([]);
  const [retData, setRetData] = useState([]);
  const [loadingReceitas, setLoadingReceitas] = useState(false);

  // POC State
  const [pocData, setPocData] = useState([]);
  const [pocEmpreendimento, setPocEmpreendimento] = useState('');
  const [pocPeriodo, setPocPeriodo] = useState('');
  const [pocPercentual, setPocPercentual] = useState('');
  const [loadingPoc, setLoadingPoc] = useState(false);

  // Compare State
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [clientes, setClientes] = useState([]);
  const [compareEmps, setCompareEmps] = useState([]);
  const [compareFiltroEmp, setCompareFiltroEmp] = useState('');

  // Llama Panel State
  const [iaFiltroEmp, setIaFiltroEmp] = useState('');
  const [iaFiltroPeriodo, setIaFiltroPeriodo] = useState('');
  const [historicoMapeamento, setHistoricoMapeamento] = useState([]);
  const [loadingHistorico, setLoadingHistorico] = useState(false);
  
  const fetchCompare = () => {
    setCompareLoading(true);
    const url = compareFiltroEmp ? `http://localhost:8000/api/compare/receitas?emp=${encodeURIComponent(compareFiltroEmp)}` : 'http://localhost:8000/api/compare/receitas';
    fetch(url)
      .then(res => res.json())
      .then(data => {
         setCompareData(data && data.timeline ? data : { timeline: [], kpis: { vgv_total: 0, distratos: 0, receita_fiscal: 0 } });
         setCompareLoading(false);
      })
      .catch(e => { console.error(e); setCompareLoading(false); });
  };

  useEffect(() => {
    if (currentView === 'compare') {
      fetchCompare();
    }
  }, [compareFiltroEmp]);
  
  const fetchClientesEEmps = () => {
    fetch('http://localhost:8000/api/compare/pessoas')
      .then(res => res.json())
      .then(data => setClientes(data.clientes || []));
      
    fetch('http://localhost:8000/api/compare/empreendimentos')
      .then(res => res.json())
      .then(data => setCompareEmps(data.empreendimentos || []));
  };

  const fetchPoc = () => {
    fetch('http://localhost:8000/api/poc')
      .then(res => res.json())
      .then(data => setPocData(data.data || []))
      .catch(err => console.error(err));
  };

  const fetchTables = (db) => {
    fetch(`http://localhost:8000/api/tables?db=${db}`)
      .then(res => res.json())
      .then(data => {
        setTables(data.tables || []);
        setSelectedTable(null);
        setTableData([]);
      })
      .catch(err => console.error("Error fetching tables", err));
  };

  useEffect(() => {
    fetchTables(selectedDb);
  }, [selectedDb]);

  useEffect(() => {
    fetch('http://localhost:8000/api/vulcano/empresas')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setGlobalEmpresas(data);
          if (data.length > 0) {
            setSelectedEmpresa(data[0].id.toString());
          }
        } else {
          setGlobalEmpresas([]);
        }
      })
      .catch(err => console.error("Erro ao buscar empresas", err));
  }, []);

  const loadTable = (tableName) => {
    setCurrentView('explorer');
    setSelectedTable(tableName);
    setLoading(true);
    fetch(`http://localhost:8000/api/table/${tableName}/data?db=${selectedDb}`)
      .then(res => res.json())
      .then(data => {
        setTableData(data.data);
        setColumns(data.columns);
        setLoading(false);
      });
  };

  const fetchReceitas = () => {
    setSelectedTable(null);
    setLoadingReceitas(true);
    fetch('http://localhost:8000/api/receitas-caixa')
      .then(res => res.json())
      .then(data => {
        setReceitasData(data.dashboard_data || []);
        setRetData(data.ret_consolidado || []);
        setLoadingReceitas(false);
      })
      .catch(err => {
        console.error("Erro ao puxar receitas", err);
        setLoadingReceitas(false);
      });
  };

  useEffect(() => {
    if (currentView === 'receitas') {
      fetchReceitas();
      fetchPoc();
    }
    if (currentView === 'poc') {
      fetchPoc();
    }
    if (currentView === 'compare') {
      fetchCompare();
      if(clientes.length === 0) fetchClientesEEmps();
    }
    if (currentView === 'llama_painel') {
      if(compareEmps.length === 0) fetchClientesEEmps();
    }
  }, [currentView]);

  useEffect(() => {
    if (iaFiltroEmp && iaFiltroPeriodo) {
      setLoadingHistorico(true);
      fetch(`http://localhost:8000/api/ia-historico-relacionado?emp=${encodeURIComponent(iaFiltroEmp)}&periodo=${encodeURIComponent(iaFiltroPeriodo)}`)
        .then(res => res.json())
        .then(data => {
          setHistoricoMapeamento(data);
          setLoadingHistorico(false);
        })
        .catch(err => {
          console.error("Erro ao buscar histórico:", err);
          setLoadingHistorico(false);
        });
    } else {
      setHistoricoMapeamento([]);
    }
  }, [iaFiltroEmp, iaFiltroPeriodo]);

  const handleSavePoc = (e) => {
    e.preventDefault();
    if (!pocEmpreendimento || !pocPeriodo || !pocPercentual) return;
    
    setLoadingPoc(true);
    fetch('http://localhost:8000/api/poc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        empreendimento: pocEmpreendimento,
        periodo: pocPeriodo,
        percentual: parseFloat(pocPercentual)
      })
    }).then(() => {
      alert('Evolução salva com sucesso!');
      fetchPoc();
      setPocEmpreendimento('');
      setPocPeriodo('');
      setPocPercentual('');
      setLoadingPoc(false);
    }).catch(err => {
      console.error("Erro ao salvar POC", err);
      alert("Erro ao salvar evolução.");
      setLoadingPoc(false);
    });
  };

  const [downloadingRazao, setDownloadingRazao] = useState(false);
  const handleRunSQL = () => {
    setDownloadingRazao(true);
    fetch('http://localhost:8000/api/export-razao')
      .then(res => res.blob())
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "Razao_Analitico_Questor.xlsx";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        setDownloadingRazao(false);
      })
      .catch(err => {
        console.error(err);
        alert("Erro ao extrair as 250 mil linhas para o Razão.");
        setDownloadingRazao(false);
      });
  };

  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');

  const filteredTables = tables.filter(t => t.toLowerCase().includes(search.toLowerCase()));

  const isDateInRange = (periodo, start, end) => {
    if (!periodo) return true;
    const pStr = typeof periodo === 'string' ? periodo.substring(0, 7) : periodo.toString().substring(0, 7);
    let valid = true;
    if (start) valid = valid && pStr >= start;
    if (end) valid = valid && pStr <= end;
    return valid;
  };

  const filteredReceitasData = receitasData.filter(r => isDateInRange(r.periodo, filterStartDate, filterEndDate));
  const filteredRetData = retData.filter(r => isDateInRange(r.periodo, filterStartDate, filterEndDate));

  const totalCaixa = filteredReceitasData.reduce((acc, r) => acc + (r.receita_caixa || 0), 0);
  const totalPisCofins = filteredReceitasData.reduce((acc, r) => acc + (r.pis || 0) + (r.cofins || 0), 0);
  const totalIrpjCsll = filteredReceitasData.reduce((acc, r) => acc + (r.irpj || 0) + (r.csll || 0), 0);
  const totalRetMacro = filteredRetData.reduce((acc, r) => acc + (r.valor_ret || 0), 0);
  const totalBaseRet = filteredRetData.reduce((acc, r) => acc + (r.base_calculo || 0), 0);
  const totalSocietario = filteredReceitasData.reduce((acc, r) => acc + (r.receita_societaria || 0), 0) + filteredRetData.reduce((acc, r) => acc + (r.receita_societaria || 0), 0);
  
  const receitaGlobal = totalCaixa + totalBaseRet;
  const allEmpreendimentos = [...receitasData.map(r => r.empreendimento), ...retData.map(r => r.empreendimento)];
  const uniqueEmpreendimentos = [...new Set(allEmpreendimentos)].filter(Boolean).sort();

  const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  return (
    <div className="flex h-screen bg-[#0b0b0b] text-[#e5e2e1] font-['Space_Grotesk'] overflow-hidden">
      {/* Sidebar - Stitch Design */}
      <aside className="w-64 bg-[#131313] border-r border-[#353534]/30 flex flex-col shrink-0 z-20">
        <div className="p-8">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 bg-[#ff4d00] rounded-sm flex items-center justify-center rotate-45 shadow-[0_0_15px_rgba(255,77,0,0.4)]">
              <Construction className="-rotate-45 text-black" size={24} />
            </div>
            <h1 className="text-2xl font-black tracking-tighter uppercase text-white">Vulcano</h1>
          </div>
          <p className="text-[10px] uppercase tracking-[0.2em] text-[#ff4d00] font-bold">Tectonic Precision</p>
        </div>

        <nav className="flex-1 overflow-y-auto">
          {/* Gestão Vulcano moved to priority 1 to verify layout */}
          <div className="px-4 space-y-2 mb-6 mt-4">
            <h3 className="text-[10px] font-bold text-[#555] uppercase tracking-widest pl-4 mb-2">Gestão Vulcano !</h3>
            <NavItem icon={<Building2 size={18}/>} label="Empreendimentos" active={currentView === 'empreendimentos'} onClick={() => setCurrentView('empreendimentos')} />
            <NavItem icon={<Users size={18}/>} label="Clientes" active={currentView === 'clientes'} onClick={() => setCurrentView('clientes')} />
            <NavItem icon={<ShoppingCart size={18}/>} label="Vendas" active={currentView === 'vendas'} onClick={() => setCurrentView('vendas')} />
            <NavItem icon={<DollarSign size={18}/>} label="Recebimentos" active={currentView === 'recebimentos'} onClick={() => setCurrentView('recebimentos')} />
          </div>

          <div className="px-4 space-y-2 mb-6 mt-4">
            <NavItem icon={<Database size={18}/>} label="Database Explorer" active={currentView === 'explorer'} onClick={() => setCurrentView('explorer')} />
            <NavItem icon={<PieChart size={18}/>} label="Receitas" active={currentView === 'receitas'} onClick={() => setCurrentView('receitas')} />
            <NavItem icon={<Construction size={18}/>} label="Evolução de Obras" active={currentView === 'poc'} onClick={() => setCurrentView('poc')} />
            <NavItem icon={<ShieldAlert size={18}/>} label="Auditoria ERP" active={currentView === 'compare'} onClick={() => setCurrentView('compare')} />
            <NavItem icon={<Zap size={18}/>} label="Conversor Univ. IA" active={currentView === 'conciliador'} onClick={() => setCurrentView('conciliador')} />
            <NavItem icon={<BrainCircuit size={18}/>} label="Mapeamento IA" active={currentView === 'llama_painel'} onClick={() => setCurrentView('llama_painel')} />
            <NavItem icon={<FileUp size={18}/>} label="Importador Inteligente" active={currentView === 'importer'} onClick={() => setCurrentView('importer')} />
          </div>
        </nav>

        <div className="p-6 border-t border-[#353534]/30">
          <button className="w-full bg-[#ff4d00] text-black py-3 rounded-sm font-bold uppercase text-xs tracking-widest hover:bg-[#ff6a00] transition-colors active:scale-95 shadow-[0_0_15px_rgba(255,77,0,0.3)]">
            + New Project
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative z-10 w-full">
        {/* Top Header */}
        <header className="h-16 border-b border-[#353534]/30 flex items-center justify-between px-8 bg-[#0b0b0b]/90 backdrop-blur-md sticky top-0 z-50 shrink-0">
          <div className="flex gap-4">
            <div className="flex items-center bg-[#131313] px-4 py-2 rounded-sm border border-[#353534]/50 w-96">
              <Search size={16} className="text-[#353534] mr-3" />
              <input 
                className="bg-transparent border-none outline-none text-sm w-full text-white placeholder-[#555]" 
                placeholder="Search projects..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            
            {/* Global Company Selector */}
            <div className="flex items-center bg-[#1a1a1c] px-4 py-2 rounded-sm border border-[#ff4d00]/50 w-96 shadow-[0_0_10px_rgba(255,77,0,0.1)]">
              <Building2 size={16} className="text-[#ff4d00] mr-3 shrink-0" />
              <select 
                value={selectedEmpresa}
                onChange={(e) => setSelectedEmpresa(e.target.value)}
                className="bg-transparent border-none outline-none text-sm w-full text-white appearance-none cursor-pointer placeholder-[#555] truncate font-bold uppercase tracking-widest"
              >
                {globalEmpresas.map(emp => (
                  <option key={emp.id} value={emp.id} className="bg-[#131313] text-white font-sans normal-case tracking-normal">
                    {emp.id} - {emp.nome}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <button className="text-[#555] hover:text-[#ff4d00] transition-colors" onClick={handleRunSQL} title="Baixar Razão Analítico"><Download size={20}/></button>
            <button className="text-[#555] hover:text-[#ff4d00] transition-colors"><Bell size={20}/></button>
            <button className="text-[#555] hover:text-[#ff4d00] transition-colors"><Settings size={20}/></button>
            <div className="flex items-center gap-3 border-l border-[#353534]/30 pl-6">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#353534] to-[#131313] border border-[#ff4d00] flex items-center justify-center overflow-hidden">
                <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=Vulcano`} alt="User" className="w-full h-full" />
              </div>
            </div>
          </div>
        </header>

        {/* View Router */}
        <div className="flex-1 overflow-y-auto p-8 relative w-full h-full">
           
           {/* =============== POC DASHBOARD (Stitch Img Match) =============== */}
           {currentView === 'poc' && (
             <div className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto w-full">
               <div className="flex justify-between items-start gap-8">
                 <div className="flex-1">
                   <h2 className="text-4xl font-bold tracking-tighter mb-4 text-white">Gerenciamento de Percentual de Conclusão</h2>
                   <p className="text-sm text-[#888] leading-relaxed max-w-3xl">Monitore o progresso técnico e financeiro em tempo real. Utilize o método POC (Percentage of Completion) para reconhecimento de receita e controle de produtividade.</p>
                 </div>
                 <div className="magma-card p-6 min-w-[300px] border-r-4 border-r-[#ff4d00] flex-shrink-0">
                   <div className="flex justify-between items-center mb-4">
                     <p className="text-[10px] uppercase tracking-widest text-[#888] font-bold">Média Global de Evolução</p>
                     <ArrowUpRight size={16} className="text-[#ff4d00]" />
                   </div>
                   <h3 className="text-6xl font-black text-[#ff4d00]">
                      {pocData.length > 0 ? (pocData.reduce((acc, curr) => acc + curr.percentual, 0) / pocData.length).toFixed(1) : '0.0'}%
                   </h3>
                   <div className="w-full h-1.5 bg-[#131313] mt-6 rounded-full overflow-hidden">
                      <div className="h-full bg-[#ff4d00] shadow-[0_0_10px_rgba(255,77,0,0.8)]" style={{width: `${pocData.length > 0 ? (pocData.reduce((acc, curr) => acc + curr.percentual, 0) / pocData.length).toFixed(1) : 0}%`}}></div>
                   </div>
                 </div>
               </div>

               <div className="grid grid-cols-12 gap-8">
                 {/* Lado Esquerdo - Formulário */}
                 <div className="col-span-4 space-y-6">
                   <div className="bg-[#131313] border border-[#222] p-8 rounded-sm relative overflow-hidden shadow-xl">
                     <div className="flex items-center gap-4 mb-8">
                       <div className="w-8 h-8 bg-[#ff4d00]/20 rounded-sm flex items-center justify-center text-[#ff4d00]">
                         <span className="font-bold text-xl">+</span>
                       </div>
                       <h3 className="text-xl font-bold text-white tracking-widest">Nova Evolução</h3>
                     </div>
                     <form onSubmit={handleSavePoc} className="space-y-6">
                       <div>
                         <label className="text-[10px] uppercase tracking-[0.2em] text-[#888] font-bold block mb-3">Empreendimento</label>
                         <select value={pocEmpreendimento} onChange={(e) => setPocEmpreendimento(e.target.value)} className="w-full bg-[#0b0b0b] border border-[#333] p-4 text-white outline-none focus:border-[#ff4d00] transition-colors rounded-sm text-sm" required>
                            <option value="">Selecione...</option>
                            {uniqueEmpreendimentos.map((emp, i) => <option key={i} value={emp}>{emp}</option>)}
                         </select>
                       </div>
                       <div>
                         <label className="text-[10px] uppercase tracking-[0.2em] text-[#888] font-bold block mb-3">Período de Referência</label>
                         <input type="month" value={pocPeriodo} onChange={(e) => setPocPeriodo(e.target.value)} className="w-full bg-[#0b0b0b] border border-[#333] p-4 text-white outline-none focus:border-[#ff4d00] transition-colors rounded-sm text-sm" required />
                       </div>
                       <div>
                         <label className="text-[10px] uppercase tracking-[0.2em] text-[#888] font-bold block mb-3">Percentual de Evolução (%)</label>
                         <div className="relative">
                           <input type="number" step="0.01" value={pocPercentual} onChange={(e) => setPocPercentual(e.target.value)} className="w-full bg-[#0b0b0b] text-4xl font-bold border border-[#333] p-4 text-white outline-none focus:border-[#ff4d00] transition-colors rounded-sm" placeholder="00.00" required />
                           <span className="absolute right-6 top-1/2 -translate-y-1/2 text-2xl font-bold text-[#444]">%</span>
                         </div>
                         <p className="text-[10px] text-[#555] italic mt-3">O percentual deve ser acumulado conforme medição de campo.</p>
                       </div>
                       <button type="submit" disabled={loadingPoc} className="w-full bg-[#ff4d00] text-black font-black uppercase tracking-[0.2em] text-xs py-4 rounded-sm hover:bg-[#ff6a00] transition-all flex justify-center items-center gap-3 mt-8 active:scale-95 shadow-[0_0_20px_rgba(255,77,0,0.2)]">
                         <ShieldAlert size={16} /> {loadingPoc ? 'Registrando...' : 'Registrar Evolução'}
                       </button>
                     </form>
                   </div>
                   <div className="bg-[#131313] border border-[#222] p-6 rounded-sm flex items-center gap-5 shadow-lg">
                      <div className="w-12 h-12 bg-[#ff4d00]/10 rounded-sm flex items-center justify-center text-[#ff4d00]">
                        <BrainCircuit size={24} />
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.2em] text-[#888] font-bold mb-1">Status de Segurança</p>
                        <h4 className="font-bold text-white tracking-widest">HSE Compliant</h4>
                      </div>
                   </div>
                 </div>

                 {/* Lado Direito - KPIs e Tabela */}
                 <div className="col-span-8 flex flex-col gap-8">
                   <div className="grid grid-cols-2 gap-6">
                      {uniqueEmpreendimentos.slice(0,4).map((emp, i) => {
                         const projPoc = pocData.filter(p => p.empreendimento === emp).sort((a,b) => b.periodo.localeCompare(a.periodo))[0];
                         const pct = projPoc ? projPoc.percentual : 0;
                         return (
                           <div key={i} className="magma-card p-6 rounded-sm flex flex-col justify-between">
                             <div className="flex justify-between items-start mb-6">
                               <div className="flex gap-4">
                                 <div className="w-10 h-10 bg-[#1a1a1a] rounded flex items-center justify-center shrink-0"><Construction size={18} className="text-[#ff4d00]" /></div>
                                 <div>
                                   <h4 className="font-bold leading-tight text-white">{emp.substring(0, 30)}</h4>
                                   <p className="text-[10px] text-[#888] uppercase tracking-[0.2em] mt-2">Fase: Fundações</p>
                                 </div>
                               </div>
                               <span className="text-2xl font-black text-white">{pct}%</span>
                             </div>
                             <div className="w-full h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden mb-4">
                                <div className="h-full bg-[#ff4d00] shadow-[0_0_10px_rgba(255,77,0,0.5)]" style={{width: `${pct}%`}}></div>
                             </div>
                             <div className="flex justify-between text-[9px] text-[#555] font-bold uppercase tracking-[0.2em]">
                                <span>Início: Mar 2024</span>
                                <span>Prev: Jan 2028</span>
                             </div>
                           </div>
                         );
                      })}
                   </div>
                   
                   <div className="bg-[#131313] border border-[#222] rounded-sm flex-1 flex flex-col shadow-xl">
                     <div className="p-6 border-b border-[#222] flex justify-between items-center bg-[#18181a]">
                       <h3 className="font-bold tracking-[0.2em] text-white uppercase text-sm">Histórico de Evolução Cadastrada</h3>
                       <div className="flex gap-2">
                         <button className="w-8 h-8 rounded bg-[#222] flex flex-col items-center justify-center gap-1 hover:bg-[#333] transition-colors"><div className="w-4 h-0.5 bg-white"></div><div className="w-4 h-0.5 bg-white"></div><div className="w-4 h-0.5 bg-white"></div></button>
                       </div>
                     </div>
                     <div className="overflow-auto flex-1">
                       <table className="w-full text-left border-collapse">
                         <thead>
                           <tr>
                             <th className="p-5 text-[10px] tracking-[0.2em] text-[#666] uppercase font-bold border-b border-[#222]">Data Reg.</th>
                             <th className="p-5 text-[10px] tracking-[0.2em] text-[#666] uppercase font-bold border-b border-[#222]">Empreendimento</th>
                             <th className="p-5 text-[10px] tracking-[0.2em] text-[#666] uppercase font-bold border-b border-[#222]">Período</th>
                             <th className="p-5 text-[10px] tracking-[0.2em] text-[#666] uppercase font-bold border-b border-[#222]">POC %</th>
                             <th className="p-5 text-[10px] tracking-[0.2em] text-[#666] uppercase font-bold border-b border-[#222]">Status</th>
                           </tr>
                         </thead>
                         <tbody>
                            {pocData.map((row, idx) => (
                              <tr key={idx} className="hover:bg-[#1a1a1a] transition-colors group">
                                <td className="p-5 border-b border-[#222] text-xs text-[#888] font-mono">15/05/2024</td>
                                <td className="p-5 border-b border-[#222] text-sm font-bold text-[#ddd]">{row.empreendimento}</td>
                                <td className="p-5 border-b border-[#222] text-xs text-[#aaa]">{row.periodo}</td>
                                <td className="p-5 border-b border-[#222] text-base font-black text-[#ff4d00] flex items-center gap-2">{row.percentual.toFixed(2)}% <ArrowUpRight size={14}/></td>
                                <td className="p-5 border-b border-[#222]">
                                  <span className="px-3 py-1 bg-[#1a3a22] text-[#4cd964] rounded-full uppercase tracking-wider border border-[#248a3d] text-[9px] font-bold">Auditado</span>
                                </td>
                              </tr>
                            ))}
                            {pocData.length === 0 && (
                              <tr><td colSpan={5} className="p-8 text-center text-[#555] italic">Nenhuma evolução registrada até o momento.</td></tr>
                            )}
                         </tbody>
                       </table>
                     </div>
                   </div>

                   <div className="bg-[#1a1a1c] border border-[#333] p-6 rounded-sm flex gap-5 items-start">
                      <div className="w-10 h-10 rounded-full bg-[#ff4d00] flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(255,77,0,0.5)]">
                        <span className="text-black font-black text-xl">!</span>
                      </div>
                      <div>
                        <h4 className="font-bold text-white tracking-widest uppercase text-sm mb-2">Aviso de Auditoria Financeira</h4>
                        <p className="text-xs text-[#888] leading-relaxed">Os percentuais de evolução registrados após o dia 10 de cada mês serão processados apenas no próximo ciclo de reconhecimento de receita (IFRS 15). Certifique-se de que o diário de obra esteja anexado.</p>
                      </div>
                   </div>
                 </div>
               </div>
             </div>
           )}

           {/* =============== Llama Painel (Nativo Modificado) =============== */}
           {currentView === 'llama_painel' && (
             <div className="space-y-6 max-w-7xl mx-auto w-full">
               <div className="flex justify-between items-center mb-6">
                 <div>
                   <h2 className="text-3xl font-bold tracking-tighter text-white uppercase flex items-center gap-3">
                     <BrainCircuit className="text-[#a259ff]" size={32} /> Painel de Mapeamento (Llama 3)
                   </h2>
                   <p className="text-sm text-[#888] mt-2">Visão integrada das tabelas operacionais e fiscais apontadas pela Inteligência Artificial.</p>
                 </div>
                 <div className="flex items-center gap-4 bg-[#131313] p-2 rounded-sm border border-[#333]">
                   <select value={iaFiltroEmp} onChange={e => setIaFiltroEmp(e.target.value)} className="bg-[#0b0b0b] text-white border border-[#444] rounded-sm px-4 py-2 text-sm outline-none">
                     <option value="">Selecione uma Empresa</option>
                     {compareEmps.map(emp => <option key={emp.id} value={emp.nome}>{emp.nome}</option>)}
                   </select>
                   <input type="month" value={iaFiltroPeriodo} onChange={e => setIaFiltroPeriodo(e.target.value)} className="bg-[#0b0b0b] text-white border border-[#444] rounded-sm px-4 py-2 text-sm outline-none" />
                   {(iaFiltroEmp || iaFiltroPeriodo) && <button onClick={() => {setIaFiltroEmp(''); setIaFiltroPeriodo('');}} className="text-[#ff4d00] font-bold text-xs uppercase px-2 hover:text-white">Limpar</button>}
                 </div>
               </div>

               <div className="magma-card overflow-hidden rounded-sm">
                 <table className="w-full text-left border-collapse">
                   <thead>
                     <tr className="bg-[#0a0a0a]">
                       <th className="p-4 text-[10px] tracking-widest text-[#ff4d00] uppercase font-bold border-b border-[#333]">Tabela Vulcano (Op)</th>
                       <th className="p-4 text-[10px] tracking-widest text-[#888] uppercase font-bold border-b border-[#333]">Sentido</th>
                       <th className="p-4 text-[10px] tracking-widest text-[#5e5ce6] uppercase font-bold border-b border-[#333]">Tabela Questor (Fiscal)</th>
                     </tr>
                   </thead>
                   <tbody>
                     <tr className="border-b border-[#222] hover:bg-[#1a1a1a]">
                       <td className="p-4 text-sm font-bold text-[#ccc]">EVOLUÇÃO DA OBRA (SQLite)</td>
                       <td className="p-4 text-sm text-[#888]">→</td>
                       <td className="p-4 text-sm font-bold text-[#ccc]">EFDINCORPIMOBRET</td>
                     </tr>
                     <tr className="border-b border-[#222] hover:bg-[#1a1a1a] bg-[#0b0b0b]/50">
                       <td className="p-4 text-sm font-bold text-[#ccc]">EXTRATO_RECEBER (Vulcano)</td>
                       <td className="p-4 text-sm text-[#888]">→</td>
                       <td className="p-4 text-sm font-bold text-[#ccc]">EFDUNIDIMOBVENDIDA</td>
                     </tr>
                   </tbody>
                 </table>
               </div>

               <div className="magma-card mt-8 rounded-sm">
                 <div className="p-6 border-b border-[#333] bg-[#131313]">
                   <h3 className="font-bold tracking-widest uppercase text-[#a259ff] text-sm flex items-center gap-2">Histórico Auditoria Cruzada IA</h3>
                 </div>
                 {loadingHistorico ? (
                   <div className="p-12 flex flex-col items-center justify-center text-[#888]">
                     <Loader2 className="animate-spin text-[#a259ff] mb-4" size={32} />
                     <p className="tracking-widest uppercase text-xs font-bold">Mapeando entidades cruzadas...</p>
                   </div>
                 ) : (
                   <div className="overflow-x-auto max-h-[500px]">
                     <table className="w-full text-left border-collapse">
                       <thead>
                         <tr>
                            <th className="p-4 text-[10px] tracking-[0.2em] text-[#666] uppercase font-bold border-b border-[#222]">Sistema</th>
                            <th className="p-4 text-[10px] tracking-[0.2em] text-[#666] uppercase font-bold border-b border-[#222]">Data</th>
                            <th className="p-4 text-[10px] tracking-[0.2em] text-[#666] uppercase font-bold border-b border-[#222] text-right">Valor (R$)</th>
                            <th className="p-4 text-[10px] tracking-[0.2em] text-[#666] uppercase font-bold border-b border-[#222]">Categoria/Unidade</th>
                         </tr>
                       </thead>
                       <tbody>
                          {historicoMapeamento.map(reg => (
                            <tr key={reg.id} className="border-b border-[#222] hover:bg-[#1a1a1a]">
                              <td className={`p-4 text-xs font-bold uppercase tracking-widest ${reg.origem === 'Questor' ? 'text-[#5e5ce6]' : 'text-[#ff4d00]'}`}>{reg.origem}</td>
                              <td className="p-4 text-sm text-[#888]">{reg.data}</td>
                              <td className="p-4 text-sm font-black text-right">{formatCurrency(reg.valor)}</td>
                              <td className="p-4 text-sm text-[#ccc]">{reg.categoria} <span className="text-[#666] text-xs">({reg.unidade})</span></td>
                            </tr>
                          ))}
                          {historicoMapeamento.length === 0 && (
                            <tr><td colSpan={4} className="p-8 text-center text-[#555] italic">Nenhum dado cruzado encontrado.</td></tr>
                          )}
                       </tbody>
                     </table>
                   </div>
                 )}
               </div>
             </div>
           )}

           {/* Outras telas (Auditoria ERP, Receitas, Questor Schema) */}
           {currentView === 'receitas' && (
             <div className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto w-full">
                <div className="flex justify-between items-end">
                  <div>
                    <h2 className="text-4xl font-bold tracking-tighter uppercase mb-2 text-white">Dashboard de Receitas</h2>
                    <p className="text-xs text-[#555] uppercase tracking-[0.3em]">Visão Financeira Consolidada • {receitaGlobal > 0 ? 'Atualizado' : 'Buscando'}</p>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-6">
                  <div className="magma-card p-6 rounded-sm">
                    <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-4">Totais Receita</p>
                    <h4 className="text-3xl font-black mb-2 text-[#e5e2e1]">{formatCurrency(receitaGlobal)}</h4>
                    <p className="text-[10px] text-[#34c759] font-bold flex items-center gap-1"><ArrowUpRight size={12}/> VGV Consolidado</p>
                  </div>
                  <div className="magma-card p-6 rounded-sm">
                    <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-4">PIS/COFINS e IRPJ/CSLL</p>
                    <h4 className="text-3xl font-black mb-2 text-[#ff4d00]">{formatCurrency(totalPisCofins + totalIrpjCsll)}</h4>
                    <p className="text-[10px] font-bold uppercase text-[#ff4d00]">• Custo Estimado</p>
                  </div>
                  <div className="magma-card p-6 rounded-sm">
                    <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-4">Total RET (4%)</p>
                    <h4 className="text-3xl font-black mb-2 text-[#ffcc00]">{formatCurrency(totalRetMacro)}</h4>
                    <p className="text-[10px] text-[#555] uppercase font-bold">Consolidado Questor</p>
                  </div>
                  <div className="magma-card p-6 rounded-sm">
                    <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-4">Receita Societária</p>
                    <h4 className="text-3xl font-black mb-2 text-[#34c759]">{formatCurrency(totalSocietario)}</h4>
                    <p className="text-[10px] text-[#555] uppercase font-bold">Aprovado Diretoria</p>
                  </div>
                </div>

                <div className="magma-card p-8 rounded-sm">
                  <h3 className="text-lg font-bold uppercase tracking-wider mb-6 text-white">Comparativo Fiscal x Societário Detalhado</h3>
                  <div className="overflow-x-auto max-h-[500px]">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr>
                          <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Empreendimento</th>
                          <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-right">Rec. Fiscal (Caixa)</th>
                          <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-right">% POC</th>
                          <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-right">Rec. Societária</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredReceitasData.length > 0 ? filteredReceitasData.map((row, i) => (
                           <tr key={i} className="border-b border-[#222] hover:bg-[#1a1a1a]">
                             <td className="p-4 text-sm font-bold text-[#ccc]">{row.empreendimento} ({row.unidade})</td>
                             <td className="p-4 text-sm text-right text-[#ffcc00] font-black">{formatCurrency(row.receita_caixa)}</td>
                             <td className="p-4 text-sm text-right text-[#555] font-bold">{row.poc}%</td>
                             <td className="p-4 text-sm text-right text-[#34c759] font-black">{formatCurrency(row.receita_societaria || 0)}</td>
                           </tr>
                        )) : <tr><td colSpan={4} className="text-center p-8 text-[#555]">Sem dados filtrados.</td></tr>}
                      </tbody>
                    </table>
                  </div>
                </div>
             </div>
           )}

           {currentView === 'compare' && (
             <div className="space-y-8 animate-in fade-in max-w-7xl mx-auto w-full">
               <h2 className="text-4xl font-bold tracking-tighter uppercase text-white mb-6">Auditoria Cruzada de ERPs</h2>
               <div className="magma-card overflow-x-auto rounded-sm p-6">
                 {compareLoading ? <Loader2 className="animate-spin text-[#ff4d00]" size={32}/> : compareData ? (
                   <table className="w-full text-left border-collapse">
                     <thead>
                       <tr>
                         <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Competência</th>
                         <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-right">Caixa(Questor)</th>
                         <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-right">Soc.(Vulcano)</th>
                         <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-right">Retidos</th>
                       </tr>
                     </thead>
                     <tbody>
                       {compareData.timeline.map((r, i) => (
                         <tr key={i} className="border-b border-[#222]">
                           <td className="p-4 text-sm text-[#888]">{r.mes}</td>
                           <td className="p-4 text-sm font-bold text-[#ffcc00] text-right">{formatCurrency(r.receita_caixa)}</td>
                           <td className="p-4 text-sm font-bold text-[#34c759] text-right">{formatCurrency(r.receita_poc)}</td>
                           <td className="p-4 text-sm font-bold text-[#ff4d00] text-right">{formatCurrency(r.impostos)}</td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 ) : <p className="text-[#555]">Carregando linha do tempo...</p>}
               </div>
             </div>
           )}

           {currentView === 'explorer' && (
             <div className="space-y-6 max-w-7xl mx-auto w-full h-full flex flex-col">
               <h2 className="text-3xl font-bold tracking-tighter uppercase text-white mb-2 flex items-center gap-3"><Database className="text-[#ff4d00]" /> Schema Explorer (Multi-DB)</h2>
               <div className="flex gap-4 h-full overflow-hidden">
                 <div className="w-64 bg-[#131313] border border-[#333] rounded-sm p-4 overflow-y-auto shrink-0">
                   <div className="flex gap-2 mb-4">
                     <button onClick={() => setSelectedDb('questor')} className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider rounded-sm ${selectedDb === 'questor' ? 'bg-[#007aff] text-white' : 'bg-[#222] text-[#888]'}`}>Questor</button>
                     <button onClick={() => setSelectedDb('vulcano')} className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider rounded-sm ${selectedDb === 'vulcano' ? 'bg-[#ff4d00] text-white' : 'bg-[#222] text-[#888]'}`}>Vulcano</button>
                   </div>
                   {filteredTables.map(t => (
                     <div key={t} onClick={() => loadTable(t)} className={`p-2 text-sm cursor-pointer border-l-2 mb-1 truncate ${selectedTable === t ? 'border-[#ff4d00] bg-[#222] text-white font-bold' : 'border-transparent text-[#888] hover:text-[#ccc]'}`}>{t}</div>
                   ))}
                 </div>
                 <div className="flex-1 bg-[#131313] border border-[#333] rounded-sm p-6 overflow-auto">
                   {selectedTable ? (
                     <table className="w-full text-left border-collapse text-sm">
                       <thead><tr>{columns.map(c => <th key={c} className="p-3 border-b border-[#333] text-[#ff4d00] uppercase text-[10px] tracking-widest">{c}</th>)}</tr></thead>
                       <tbody>
                         {tableData.slice(0, 100).map((r, i) => <tr key={i} className="border-b border-[#222] hover:bg-[#1a1a1a]">{columns.map(c => <td key={c} className="p-3 text-[#ccc] truncate max-w-[200px]">{r[c]}</td>)}</tr>)}
                       </tbody>
                     </table>
                   ) : <div className="flex items-center justify-center h-full text-[#555] font-bold tracking-widest uppercase">Selecione uma tabela</div>}
                 </div>
               </div>
             </div>
           )}

           {/* Novas Telas Vulcano */}
           {currentView === 'empreendimentos' && <EmpreendimentosView selectedEmpresa={selectedEmpresa} />}
           {currentView === 'clientes' && <ClientesView selectedEmpresa={selectedEmpresa} />}
           {currentView === 'vendas' && <VendasView selectedEmpresa={selectedEmpresa} />}
           {currentView === 'recebimentos' && <RecebimentosView selectedEmpresa={selectedEmpresa} />}
           {currentView === 'importer' && <SmartImporter selectedEmpresa={selectedEmpresa} />}
           {currentView === 'conciliador' && <ConciliadorView />}

        </div>
      </main>
    </div>
  );
}

// Stitch Helper
const NavItem = ({ icon, label, active, onClick }) => (
  <button 
    onClick={onClick}
    className={`w-full flex items-center gap-4 px-4 py-3 rounded-sm transition-all duration-300 group ${
      active ? 'bg-[#1a1a1a] text-[#ff4d00] border-r-2 border-[#ff4d00] shadow-[0_0_20px_rgba(255,77,0,0.1)]' : 'text-[#555] hover:text-[#e5e2e1]'
    }`}
  >
    <span className={`${active ? 'text-[#ff4d00]' : 'group-hover:text-[#ff4d00]'} transition-colors`}>{icon}</span>
    <span className="text-[10px] uppercase tracking-widest font-bold">{label}</span>
  </button>
);

export default App;
// cache buster
