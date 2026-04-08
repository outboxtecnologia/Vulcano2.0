import React, { useState, useEffect } from 'react';
import { Building2, Users, ShoppingCart, DollarSign, Filter, Search, ArrowUpRight, ArrowDownRight, AlertCircle, CheckCircle, CheckCircle2, Loader2, Plus, Download, Zap, FileText, UploadCloud, MessageSquare, Send, Save, Database, Code } from 'lucide-react';

const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
const API_BASE = import.meta?.env?.VITE_API_BASE || 'http://127.0.0.1:8002';

export const EmpreendimentosView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [activeTab, setActiveTab] = useState('principal');
  
  const [contas, setContas] = useState([]);
  const [centros, setCentros] = useState([]);
  const [historicos, setHistoricos] = useState([]);
  const [questorLoading, setQuestorLoading] = useState(false);

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => {
        setData(Array.isArray(d) ? d : []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedEmpresa]);

  useEffect(() => {
    if (showForm && contas.length === 0) {
      setQuestorLoading(true);
      Promise.all([
        fetch(`${API_BASE}/api/questor/contas`).then(r => r.json()),
        fetch(`${API_BASE}/api/questor/centrocusto`).then(r => r.json()),
        fetch(`${API_BASE}/api/questor/historicos`).then(r => r.json())
      ]).then(([c, cc, h]) => {
        setContas(c);
        setCentros(cc);
        setHistoricos(h);
        setQuestorLoading(false);
      }).catch(err => {
        console.error(err);
        setQuestorLoading(false);
      });
    }
  }, [showForm, contas.length]);

  const totalOrcado = data.reduce((acc, curr) => acc + (curr.custo || 0), 0);
  const totaisRet = data.filter(d => d.ret === 'S').length;

  return (
    <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tighter uppercase mb-2 text-white flex items-center gap-3"><Building2 className="text-[#ff4d00]" size={28}/> Cadastro de Empreendimentos</h2>
          <p className="text-xs text-[#555] uppercase tracking-[0.3em]">Listagem de Obras e Status Fiscal</p>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-1">Total Orçado {selectedEmpresa}</p>
            <h3 className="text-2xl font-black text-[#ff4d00]">{formatCurrency(totalOrcado)}</h3>
          </div>
          <button onClick={() => setShowForm(!showForm)} className="bg-[#ff4d00] text-white text-[10px] font-bold uppercase tracking-widest px-4 py-2 rounded-sm hover:opacity-80 transition-opacity flex items-center gap-2">
            <Plus size={14}/> Cadastrar
          </button>
        </div>
      </div>
      
      {showForm && (
        <div className="bg-[#131313] border border-[#ff4d00]/50 rounded-sm p-4 animate-in fade-in slide-in-from-top-4 flex flex-col">
          <h3 className="text-xs uppercase tracking-widest text-[#ff4d00] font-bold mb-4">Novo Empreendimento</h3>
          
          <div className="flex gap-4 mb-6 border-b border-[#333] pb-2">
            <button onClick={() => setActiveTab('principal')} className={`text-xs font-bold uppercase tracking-widest px-3 py-1 transition-colors ${activeTab === 'principal' ? 'text-[#ff4d00] border-b-2 border-[#ff4d00]' : 'text-[#888] hover:text-[#ccc]'}`}>Principal</button>
            <button onClick={() => setActiveTab('contas')} className={`text-xs font-bold uppercase tracking-widest px-3 py-1 transition-colors ${activeTab === 'contas' ? 'text-[#ff4d00] border-b-2 border-[#ff4d00]' : 'text-[#888] hover:text-[#ccc]'}`}>Contas Contábeis</button>
            <button onClick={() => setActiveTab('historicos')} className={`text-xs font-bold uppercase tracking-widest px-3 py-1 transition-colors ${activeTab === 'historicos' ? 'text-[#ff4d00] border-b-2 border-[#ff4d00]' : 'text-[#888] hover:text-[#ccc]'}`}>Históricos</button>
            <button onClick={() => setActiveTab('unidades')} className={`text-xs font-bold uppercase tracking-widest px-3 py-1 transition-colors ${activeTab === 'unidades' ? 'text-[#ff4d00] border-b-2 border-[#ff4d00]' : 'text-[#888] hover:text-[#ccc]'}`}>Blocos/Unidades</button>
          </div>

          <form className="flex flex-col gap-4" onSubmit={async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            try {
              await fetch("http://localhost:8001/api/empreendimentos", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(fd)) });
              alert("Empreendimento cadastrado!"); e.target.reset(); setShowForm(false);
            } catch (err) { alert("Erro ao cadastrar."); }
          }}>
            
            <div className={activeTab === 'principal' ? 'flex flex-col gap-4' : 'hidden'}>
              <div className="flex gap-4">
                <div className="flex-1"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Nome</label><input name="nome" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
                <div className="w-32"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Metragem</label><input name="metragem" type="number" step="0.01" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
                <div className="w-40"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Custo Orçado</label><input name="custo" type="number" step="0.01" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
              </div>
              <div className="flex gap-4">
                <div className="w-32"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">RET</label><select name="ret" className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white"><option value="N">Não</option><option value="S">Sim</option></select></div>
              </div>
            </div>

            <div className={activeTab === 'contas' ? 'flex flex-col gap-4 relative min-h-[100px]' : 'hidden'}>
              {questorLoading && <div className="absolute inset-0 bg-[#131313]/80 backdrop-blur-sm flex items-center justify-center z-10"><Loader2 className="animate-spin text-[#ff4d00]" size={24} /></div>}
              <div className="flex gap-4">
                <div className="flex-1"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Conta Caixa/Bancos</label>
                  <select name="conta_caixa" className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white">
                    <option value="">Selecione a conta...</option>
                    {contas.map(c => <option key={c.id} value={c.id}>{c.id} - {c.descricao}</option>)}
                  </select>
                </div>
                <div className="flex-1"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Conta Clientes</label>
                  <select name="conta_clientes" className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white">
                    <option value="">Selecione a conta...</option>
                    {contas.map(c => <option key={c.id} value={c.id}>{c.id} - {c.descricao}</option>)}
                  </select>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex-1"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Centro de Custo Padrão</label>
                  <select name="centro_custo" className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white">
                    <option value="">Selecione o centro de custo...</option>
                    {centros.map(cc => <option key={cc.id} value={cc.id}>{cc.id} - {cc.descricao}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <div className={activeTab === 'historicos' ? 'flex flex-col gap-4 relative min-h-[100px]' : 'hidden'}>
              {questorLoading && <div className="absolute inset-0 bg-[#131313]/80 backdrop-blur-sm flex items-center justify-center z-10"><Loader2 className="animate-spin text-[#ff4d00]" size={24} /></div>}
              <div className="flex gap-4">
                <div className="flex-1"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Histórico Padrão Recebimento</label>
                  <select name="hist_recebimento" className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white">
                    <option value="">Selecione histórico...</option>
                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                  </select>
                </div>
                <div className="flex-1"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Histórico Padrão Distrato</label>
                  <select name="hist_distrato" className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white">
                    <option value="">Selecione histórico...</option>
                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <div className={activeTab === 'unidades' ? 'flex flex-col gap-4' : 'hidden'}>
              <p className="text-xs text-[#888] italic">Módulo de unidades será ativado após o primeiro salvamento do Empreendimento.</p>
            </div>

            <div className="flex justify-end mt-4">
              <button type="submit" className="bg-[#ff4d00] text-white text-[10px] font-bold uppercase tracking-widest px-6 py-2 rounded-sm hover:opacity-80">Salvar Empreendimento</button>
            </div>
          </form>
        </div>
      )}
      <div className="bg-[#131313] border border-[#333] rounded-sm flex-1 flex flex-col overflow-hidden shadow-xl">
        <div className="p-4 border-b border-[#222] bg-[#0a0a0a] flex justify-between items-center">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#888]">
            <Search size={14}/> <span>Filtrar Projetos</span>
          </div>
          <div className="text-[10px] uppercase tracking-widest font-bold text-[#888]">
            {data.length} Projetos Encontrados ({totaisRet} RET)
          </div>
        </div>
        <div className="overflow-auto flex-1 relative">
          {loading && (
            <div className="absolute inset-0 bg-[#131313]/80 backdrop-blur-sm flex flex-col items-center justify-center z-10">
              <Loader2 className="animate-spin text-[#ff4d00] mb-4" size={32} />
              <span className="text-xs font-bold uppercase tracking-widest text-[#888]">Carregando Dados do ERP...</span>
            </div>
          )}
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr>
                <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">ID</th>
                <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Nome</th>
                <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-right">Metragem Total</th>
                <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-right">Custo Orçado</th>
                <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-center">RET</th>
                <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Data Conclusão</th>
                <th className="p-4 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-center">Ativo</th>
              </tr>
            </thead>
            <tbody>
              {data.map((emp) => (
                <tr key={emp.id} className="border-b border-[#222] hover:bg-[#1a1a1a]">
                  <td className="p-4 text-[#888]">{emp.id}</td>
                  <td className="p-4 font-bold text-[#ccc]">{emp.nome}</td>
                  <td className="p-4 text-right text-[#aaa]">{emp.metragem ? emp.metragem.toLocaleString('pt-BR') : '-'}</td>
                  <td className="p-4 text-right font-black text-[#e5e2e1]">{emp.custo ? formatCurrency(emp.custo) : '-'}</td>
                  <td className="p-4 text-center">
                    <div className={`w-3 h-3 rounded-full mx-auto ${emp.ret === 'S' ? 'bg-[#ff4d00] shadow-[0_0_8px_rgba(255,77,0,0.8)]' : 'bg-[#333]'}`}></div>
                  </td>
                  <td className="p-4 text-[#888]">{emp.data_conclusao || '-'}</td>
                  <td className="p-4 text-center">
                    <div className={`w-3 h-3 rounded-full mx-auto ${emp.ativo === 'S' ? 'bg-[#34c759] shadow-[0_0_8px_rgba(52,199,89,0.5)]' : 'bg-[#333]'}`}></div>
                  </td>
                </tr>
              ))}
              {!loading && data.length === 0 && (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-[#555] italic">Nenhum empreendimento encontrado para esta empresa.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export const ClientesView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/clientes?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => {
        setData(Array.isArray(d) ? d : []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedEmpresa]);

  const filtered = data.filter(c => c.nome.toLowerCase().includes(search.toLowerCase()) || (c.cpf_cnpj && c.cpf_cnpj.includes(search)));

  return (
    <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tighter uppercase mb-2 text-white flex items-center gap-3"><Users className="text-[#a259ff]" size={28}/> Cadastro de Clientes</h2>
          <p className="text-xs text-[#555] uppercase tracking-[0.3em]">Gestão de Compradores e Parceiros</p>
        </div>
      </div>
      <div className="bg-[#131313] border border-[#333] rounded-sm flex-1 flex flex-col overflow-hidden shadow-xl max-w-4xl">
        <div className="p-4 border-b border-[#222] bg-[#0a0a0a] flex justify-between items-center">
          <div className="flex items-center gap-3 w-96 bg-[#0b0b0b] border border-[#333] rounded-sm px-3 py-2 focus-within:border-[#a259ff] transition-colors">
            <Search size={14} className="text-[#555]"/> 
            <input 
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Buscar por nome ou CPF/CNPJ..."
              className="bg-transparent border-none outline-none w-full text-xs text-white placeholder-[#555]"
            />
          </div>
          <div className="text-[10px] uppercase tracking-widest font-bold text-[#888]">
            {filtered.length} Clientes Encontrados
          </div>
        </div>
        <div className="overflow-auto flex-1 relative">
          {loading && (
            <div className="absolute inset-0 bg-[#131313]/80 backdrop-blur-sm flex flex-col items-center justify-center z-10">
              <Loader2 className="animate-spin text-[#a259ff] mb-4" size={32} />
              <span className="text-xs font-bold uppercase tracking-widest text-[#888]">Sincronizando Base Vulcano...</span>
            </div>
          )}
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr>
                <th className="p-4 text-[10px] tracking-widest text-[#a259ff] uppercase font-bold border-b border-[#333] w-24">Código</th>
                <th className="p-4 text-[10px] tracking-widest text-[#a259ff] uppercase font-bold border-b border-[#333]">Nome Completo / Razão Social</th>
                <th className="p-4 text-[10px] tracking-widest text-[#a259ff] uppercase font-bold border-b border-[#333] w-48">CPF / CNPJ</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 100).map((c) => (
                <tr key={c.id} className="border-b border-[#222] hover:bg-[#1a1a1a]">
                  <td className="p-4 text-[#888] font-mono">{c.id}</td>
                  <td className="p-4 font-bold text-[#ccc]">{c.nome}</td>
                  <td className="p-4 text-[#aaa] font-mono">{c.cpf_cnpj}</td>
                </tr>
              ))}
              {!loading && filtered.length > 100 && (
                <tr>
                  <td colSpan="3" className="p-4 text-center text-[#a259ff] text-xs font-bold uppercase tracking-widest">Exibindo 100 primeiros registros. Digite na busca para refinar.</td>
                </tr>
              )}
              {!loading && filtered.length === 0 && (
                <tr>
                  <td colSpan="3" className="p-8 text-center text-[#555] italic">Nenhum cliente encontrado.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export const VendasView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [distratoModal, setDistratoModal] = useState(null);
  const [condicoesModal, setCondicoesModal] = useState(null); // { venda, payload, loading, error }
  
  const [compradores, setCompradores] = useState([{ id: Date.now(), nome: '', cpf_cnpj: '', percentual: 100 }]);
  const [parcelas, setParcelas] = useState([{ id: Date.now() + 1, vencimento: '', valor: '' }]);

  const openCondicoes = async (venda) => {
    setCondicoesModal({ venda, payload: null, loading: true, error: '' });
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/${encodeURIComponent(venda.id)}/condicoes`);
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
      setCondicoesModal({ venda, payload: json, loading: false, error: '' });
    } catch (e) {
      console.error(e);
      setCondicoesModal({ venda, payload: null, loading: false, error: e.message || 'Falha ao carregar condições.' });
    }
  };

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => {
        setData(Array.isArray(d) ? d : []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedEmpresa]);

  const uniqueEmps = [...new Set(data.map(v => v.empreendimento))].sort();
  const filtered = data.filter(v => !empreendimentoFilter || v.empreendimento === empreendimentoFilter);

  const totalVgv = filtered.reduce((acc, curr) => acc + (curr.total || 0), 0);
  const totalDistratos = filtered.filter(v => v.distrato === 'S').reduce((acc, curr) => acc + (curr.total || 0), 0);

  const addComprador = () => {
    setCompradores([...compradores, { id: Date.now(), nome: '', cpf_cnpj: '', percentual: 0 }]);
  };
  
  const updateComprador = (id, field, value) => {
    setCompradores(compradores.map(c => c.id === id ? { ...c, [field]: value } : c));
  };

  const removeComprador = (id) => {
    setCompradores(compradores.filter(c => c.id !== id));
  };

  const addParcela = () => {
    setParcelas([...parcelas, { id: Date.now(), vencimento: '', valor: '' }]);
  };

  const updateParcela = (id, field, value) => {
    setParcelas(parcelas.map(p => p.id === id ? { ...p, [field]: value } : p));
  };

  const removeParcela = (id) => {
    setParcelas(parcelas.filter(p => p.id !== id));
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd);
    payload.compradores = compradores;
    payload.parcelas = parcelas;
    
    try {
      await fetch("http://localhost:8001/api/vendas", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      alert("Venda cadastrada!"); 
      e.target.reset(); 
      setCompradores([{ id: Date.now(), nome: '', cpf_cnpj: '', percentual: 100 }]);
      setParcelas([{ id: Date.now() + 1, vencimento: '', valor: '' }]);
      setShowForm(false);
    } catch (err) { alert("Erro ao cadastrar."); }
  };

  return (
    <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tighter uppercase mb-2 text-white flex items-center gap-3"><ShoppingCart className="text-[#007aff]" size={28}/> Painel de Vendas</h2>
          <p className="text-xs text-[#555] uppercase tracking-[0.3em]">Unidades Comercializadas e Distratos</p>
        </div>
        <div className="flex gap-6 text-right">
          <div>
            <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-1">VGV Período/Empresa</p>
            <h3 className="text-2xl font-black text-[#007aff]">{formatCurrency(totalVgv)}</h3>
          </div>
          <div className="border-l border-[#333] pl-6">
            <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-1">Distratos Lançados</p>
            <h3 className="text-2xl font-black text-[#ff4d00]">{formatCurrency(totalDistratos)}</h3>
          </div>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="bg-[#007aff] text-white text-[10px] font-bold uppercase tracking-widest px-4 py-2 rounded-sm hover:opacity-80 transition-opacity flex items-center gap-2 self-end mb-1 ml-6">
          <Plus size={14}/> Cadastrar Venda
        </button>
      </div>
      
      {showForm && (
        <div className="bg-[#131313] border border-[#007aff]/50 rounded-sm p-4 animate-in fade-in slide-in-from-top-4 overflow-y-auto max-h-[60vh] custom-scrollbar">
          <div className="flex justify-between items-center mb-4 border-b border-[#333] pb-2">
            <h3 className="text-xs uppercase tracking-widest text-[#007aff] font-bold">Nova Venda</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-[#888] hover:text-white text-[10px] uppercase tracking-widest font-bold">FECHAR X</button>
          </div>
          
          <form className="flex flex-col gap-6" onSubmit={handleFormSubmit}>
            
            {/* DADOS GERAIS */}
            <div className="flex gap-4">
              <div className="w-24"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">ID Emp.</label><input name="id_empreendimento" type="number" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
              <div className="w-32"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Unidade</label><input name="unidade" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
              <div className="flex-1"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Total Venda</label><input name="total" type="number" step="0.01" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
              <div className="w-40"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Data Venda</label><input name="data" type="date" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
            </div>

            {/* MÚLTIPLOS COMPRADORES */}
            <div className="border border-[#222] bg-[#0a0a0a] p-3 rounded-sm">
              <div className="flex justify-between items-center mb-3">
                <h4 className="text-[10px] text-[#888] uppercase tracking-widest font-bold flex items-center gap-2"><Users size={12}/> Compradores / Sociedade</h4>
                <button type="button" onClick={addComprador} className="text-[#007aff] hover:text-white text-[10px] font-bold uppercase tracking-widest flex items-center gap-1"><Plus size={12}/> Adicionar Comprador</button>
              </div>
              <div className="flex flex-col gap-3">
                {compradores.map((comp, idx) => (
                  <div key={comp.id} className="flex gap-3 items-end">
                    <div className="flex-1"><label className="text-[10px] text-[#555] uppercase tracking-widest block mb-1">Nome/Razão Social</label><input value={comp.nome} onChange={(e) => updateComprador(comp.id, 'nome', e.target.value)} required className="w-full bg-[#131313] border border-[#333] p-2 text-xs text-white" /></div>
                    <div className="w-40"><label className="text-[10px] text-[#555] uppercase tracking-widest block mb-1">CPF/CNPJ</label><input value={comp.cpf_cnpj} onChange={(e) => updateComprador(comp.id, 'cpf_cnpj', e.target.value)} required className="w-full bg-[#131313] border border-[#333] p-2 text-xs text-white" /></div>
                    <div className="w-24"><label className="text-[10px] text-[#555] uppercase tracking-widest block mb-1">% Compra</label><input type="number" step="0.01" value={comp.percentual} onChange={(e) => updateComprador(comp.id, 'percentual', parseFloat(e.target.value) || 0)} required className="w-full bg-[#131313] border border-[#333] p-2 text-xs text-white text-right" /></div>
                    {compradores.length > 1 && (
                      <button type="button" onClick={() => removeComprador(comp.id)} className="bg-[#ff4d00]/10 text-[#ff4d00] border border-[#ff4d00]/30 hover:bg-[#ff4d00] hover:text-white p-2 rounded-sm mb-[1px] transition-colors"><AlertCircle size={14}/></button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* FLUXO DE PARCELAS */}
            <div className="border border-[#222] bg-[#0a0a0a] p-3 rounded-sm">
              <div className="flex justify-between items-center mb-3">
                <h4 className="text-[10px] text-[#888] uppercase tracking-widest font-bold flex items-center gap-2"><DollarSign size={12}/> Condições de Pagamento (Parcelas a Vencer)</h4>
                <button type="button" onClick={addParcela} className="text-[#34c759] hover:text-white text-[10px] font-bold uppercase tracking-widest flex items-center gap-1"><Plus size={12}/> Nova Parcela</button>
              </div>
              <div className="flex flex-col gap-1 w-full max-w-md">
                <div className="flex gap-3 px-1 mb-1">
                  <span className="flex-1 text-[10px] text-[#555] uppercase tracking-widest font-bold">Data Vencimento</span>
                  <span className="flex-1 text-[10px] text-[#555] uppercase tracking-widest font-bold">Valor Previsto</span>
                  <span className="w-8"></span>
                </div>
                {parcelas.map((parc, idx) => (
                  <div key={parc.id} className="flex gap-3 items-center">
                    <input type="date" value={parc.vencimento} onChange={(e) => updateParcela(parc.id, 'vencimento', e.target.value)} required className="flex-1 bg-[#131313] border border-[#333] p-1.5 text-xs text-white" />
                    <input type="number" step="0.01" value={parc.valor} onChange={(e) => updateParcela(parc.id, 'valor', e.target.value)} required className="flex-1 bg-[#131313] border border-[#333] p-1.5 text-xs text-white" placeholder="R$" />
                    {parcelas.length > 1 ? (
                      <button type="button" onClick={() => removeParcela(parc.id)} className="text-[#ff4d00] hover:text-white w-8 flex justify-center"><AlertCircle size={12}/></button>
                    ) : <span className="w-8"></span>}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end mt-2">
              <button type="submit" className="bg-[#007aff] text-white text-[10px] font-bold uppercase tracking-widest px-8 py-3 rounded-sm hover:opacity-80 transition-opacity">Registrar Contrato de Venda</button>
            </div>
          </form>
        </div>
      )}

      <div className="flex gap-6 h-full overflow-hidden">
        <div className="w-64 bg-[#131313] border border-[#333] rounded-sm flex flex-col shrink-0">
          <div className="p-4 border-b border-[#333] bg-[#0a0a0a]">
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-[#555]">Filtro Empreendimento</h3>
          </div>
          <div className="overflow-y-auto flex-1 p-2">
            <div 
              onClick={() => setEmpreendimentoFilter('')}
              className={`p-3 text-xs font-bold cursor-pointer transition-colors ${empreendimentoFilter === '' ? 'text-white bg-[#007aff]/10 border-l-2 border-[#007aff]' : 'text-[#888] hover:text-white hover:bg-[#1a1a1a] border-l-2 border-transparent'}`}
            >
              &lt;&lt;&lt; Todos &gt;&gt;&gt;
            </div>
            {uniqueEmps.map((emp, i) => (
              <div 
                key={i} 
                onClick={() => setEmpreendimentoFilter(emp)}
                className={`p-3 text-xs cursor-pointer transition-colors truncate ${empreendimentoFilter === emp ? 'text-white bg-[#007aff]/10 border-l-2 border-[#007aff] font-bold' : 'text-[#888] hover:text-white hover:bg-[#1a1a1a] border-l-2 border-transparent'}`} 
                title={emp}
              >
                {emp || 'Indefinido'}
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 bg-[#131313] border border-[#333] rounded-sm flex flex-col overflow-hidden shadow-xl">
          <div className="overflow-auto flex-1 relative">
            {loading && (
              <div className="absolute inset-0 bg-[#131313]/80 backdrop-blur-sm flex flex-col items-center justify-center z-10">
                <Loader2 className="animate-spin text-[#007aff] mb-4" size={32} />
                <span className="text-xs font-bold uppercase tracking-widest text-[#888]">Integrando Vendas...</span>
              </div>
            )}
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-[#0a0a0a]">
                  <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Venda/Contrato</th>
                  <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Data Venda</th>
                  <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Descrição/Unidade</th>
                  <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">CPF/CNPJ</th>
                  <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Cliente</th>
                  <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-right">Total Venda</th>
                  <th className="p-3 text-[10px] tracking-widest text-[#34c759] uppercase font-bold border-b border-[#333] text-center">Condições</th>
                  <th className="p-3 text-[10px] tracking-widest text-[#ff4d00] uppercase font-bold border-b border-[#333] text-center">Distrato</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((v) => (
                  <tr key={v.id} className={`border-b border-[#222] hover:bg-[#1a1a1a] ${v.distrato === 'S' ? 'text-[#ff4d00]/70' : 'text-[#ccc]'}`}>
                    <td className="p-3 font-mono text-[#888]">{v.id} <span className="text-[#555] ml-1">#{v.num_cad}</span></td>
                    <td className="p-3">{v.data}</td>
                    <td className="p-3 font-bold truncate max-w-[200px]" title={v.descricao}>{v.descricao}</td>
                    <td className="p-3 font-mono text-xs text-[#888]">{v.cliente_cnpj}</td>
                    <td className="p-3 truncate max-w-[150px]" title={v.cliente_nome}>{v.cliente_nome}</td>
                    <td className={`p-3 text-right font-black ${v.distrato === 'S' ? 'text-[#ff4d00]' : 'text-[#34c759]'}`}>{formatCurrency(v.total)}</td>
                    <td className="p-3 text-center">
                      <button
                        type="button"
                        onClick={() => openCondicoes(v)}
                        className="text-[10px] uppercase font-bold text-[#34c759] hover:text-black border border-[#34c759]/40 hover:bg-[#34c759] px-2 py-1 rounded transition-colors"
                        title="Ver condições de pagamento, parcelas, entrada/reforços (se existir)"
                      >
                        Ver
                      </button>
                    </td>
                    <td className="p-3 text-center">
                      {v.distrato === 'S' ? (
                        <span className="text-[#ff4d00] font-bold uppercase text-[10px] tracking-widest bg-[#ff4d00]/10 border border-[#ff4d00]/20 px-2 py-1 rounded">Distrato</span>
                      ) : (
                        <button onClick={() => setDistratoModal(v)} className="text-[10px] uppercase font-bold text-[#888] hover:text-[#ff4d00] border border-[#333] hover:border-[#ff4d00]/50 px-2 py-1 rounded transition-colors">Distratar</button>
                      )}
                    </td>
                  </tr>
                ))}
                {!loading && filtered.length === 0 && (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-[#555] italic">Nenhuma venda encontrada para este filtro.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {distratoModal && (
        <div className="fixed inset-0 bg-[#131313]/90 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in">
          <div className="bg-[#0a0a0a] border border-[#ff4d00] p-6 rounded-sm max-w-md w-full">
            <h3 className="text-sm uppercase tracking-widest text-[#ff4d00] font-bold mb-4">Registrar Distrato</h3>
            <div className="bg-[#131313] p-3 border border-[#333] rounded-sm mb-4">
              <p className="text-[10px] uppercase tracking-widest text-[#888] font-bold mb-1">Venda Selecionada</p>
              <p className="text-xs font-bold text-white block truncate mb-1">{distratoModal.descricao}</p>
              <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold">Cliente: {distratoModal.cliente_nome}</p>
            </div>
            
            <form className="flex flex-col gap-4" onSubmit={async (e) => {
              e.preventDefault();
              const fd = new FormData(e.target);
              fd.append('id_venda', distratoModal.id);
              try {
                await fetch(`${API_BASE}/api/distratos`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(fd)) });
                alert("Distrato registrado!"); 
                setDistratoModal(null);
                // Optionally trigger reload of data
              } catch (err) { alert("Erro ao registrar distrato."); }
            }}>
              <div>
                <label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Data do Distrato</label>
                <input name="data_distrato" type="date" required className="w-full bg-[#131313] border border-[#333] p-2 text-xs text-white" />
              </div>
              <div>
                <label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Valor a Devolver</label>
                <input name="valor_devolvido" type="number" step="0.01" required className="w-full bg-[#131313] border border-[#333] p-2 text-xs text-white" />
              </div>
              <div>
                <label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Data Previsão Pagto</label>
                <input name="data_pagamento" type="date" required className="w-full bg-[#131313] border border-[#333] p-2 text-xs text-white" />
              </div>
              <div className="flex justify-end gap-3 mt-4">
                <button type="button" onClick={() => setDistratoModal(null)} className="text-[#888] hover:text-white text-[10px] font-bold uppercase tracking-widest px-4 py-2 hover:bg-[#1a1a1a] rounded transition-colors">Cancelar</button>
                <button type="submit" className="bg-[#ff4d00] text-white text-[10px] font-bold uppercase tracking-widest px-6 py-2 rounded-sm hover:opacity-80 transition-opacity">Confirmar Distrato</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {condicoesModal && (
        <div className="fixed inset-0 bg-[#131313]/90 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in">
          <div className="bg-[#0a0a0a] border border-[#34c759]/40 p-6 rounded-sm max-w-5xl w-[95vw] max-h-[85vh] overflow-hidden flex flex-col">
            <div className="flex items-start justify-between gap-4 border-b border-[#222] pb-3">
              <div className="min-w-0">
                <h3 className="text-sm uppercase tracking-widest text-[#34c759] font-bold">Condições / Parcelas</h3>
                <p className="text-[10px] uppercase tracking-widest text-[#666] font-bold mt-1 truncate">
                  Venda #{condicoesModal.venda?.id} · {condicoesModal.venda?.descricao}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setCondicoesModal(null)}
                className="text-[#888] hover:text-white text-[10px] uppercase tracking-widest font-bold"
              >
                FECHAR X
              </button>
            </div>

            <div className="flex-1 overflow-auto custom-scrollbar mt-4 space-y-6">
              {condicoesModal.loading && (
                <div className="flex items-center gap-3 text-[#888] text-xs font-bold uppercase tracking-widest">
                  <Loader2 className="animate-spin" size={18} /> Carregando condições...
                </div>
              )}
              {!condicoesModal.loading && condicoesModal.error && (
                <div className="bg-[#131313] border border-[#ff4d00]/40 p-3 rounded-sm text-[#ff4d00] text-xs font-bold uppercase tracking-widest">
                  {condicoesModal.error}
                </div>
              )}

              {!condicoesModal.loading && condicoesModal.payload && (
                <>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-[#131313] border border-[#222] p-3 rounded-sm">
                      <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-1">Total Venda</p>
                      <p className="text-lg font-black text-[#34c759]">{formatCurrency(condicoesModal.payload.venda?.total || 0)}</p>
                    </div>
                    <div className="bg-[#131313] border border-[#222] p-3 rounded-sm">
                      <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-1">Cliente</p>
                      <p className="text-xs font-bold text-white truncate" title={condicoesModal.payload.venda?.cliente?.nome}>
                        {condicoesModal.payload.venda?.cliente?.nome || '-'}
                      </p>
                      <p className="text-[10px] uppercase tracking-widest text-[#777] font-bold mt-1">
                        {condicoesModal.payload.venda?.cliente?.cnpj || ''}
                      </p>
                    </div>
                    <div className="bg-[#131313] border border-[#222] p-3 rounded-sm">
                      <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-1">Empreendimento</p>
                      <p className="text-xs font-bold text-white truncate" title={condicoesModal.payload.venda?.empreendimento}>
                        {condicoesModal.payload.venda?.empreendimento || '-'}
                      </p>
                      <p className="text-[10px] uppercase tracking-widest text-[#777] font-bold mt-1">
                        Data: {condicoesModal.payload.venda?.data || '-'}
                      </p>
                    </div>
                  </div>

                  <div className="bg-[#131313] border border-[#222] rounded-sm overflow-hidden">
                    <div className="p-3 bg-[#0a0a0a] border-b border-[#222]">
                      <h4 className="text-[10px] uppercase tracking-widest text-[#34c759] font-bold">Formas de pagamento (condição)</h4>
                    </div>
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-[#0f0f0f]">
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222]">Descrição</th>
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222] text-right">Valor</th>
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222] text-center">Qtd</th>
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222] text-center">Ativa</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(condicoesModal.payload.formas_pagto || []).map((f) => (
                          <tr key={f.id} className="border-b border-[#1f1f1f] hover:bg-[#111] text-[#ddd]">
                            <td className="p-3 font-bold">{f.descricao || '-'}</td>
                            <td className="p-3 text-right font-mono">{formatCurrency(f.valor || 0)}</td>
                            <td className="p-3 text-center font-mono text-[#888]">{f.quantidade_parcelas || 0}</td>
                            <td className="p-3 text-center">
                              <span className={`text-[10px] uppercase tracking-widest font-bold px-2 py-1 rounded border ${f.ativa === 'S' ? 'text-[#34c759] border-[#34c759]/30 bg-[#34c759]/10' : 'text-[#888] border-[#333] bg-[#0a0a0a]'}`}>
                                {f.ativa === 'S' ? 'Ativa' : 'Inativa'}
                              </span>
                            </td>
                          </tr>
                        ))}
                        {(condicoesModal.payload.formas_pagto || []).length === 0 && (
                          <tr>
                            <td colSpan="4" className="p-4 text-center text-[#666] italic">Nenhuma forma de pagamento cadastrada para esta venda.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  <div className="bg-[#131313] border border-[#222] rounded-sm overflow-hidden">
                    <div className="p-3 bg-[#0a0a0a] border-b border-[#222] flex items-center justify-between">
                      <h4 className="text-[10px] uppercase tracking-widest text-[#34c759] font-bold">Parcelas (RECEBER)</h4>
                      <span className="text-[10px] uppercase tracking-widest text-[#666] font-bold">
                        {(condicoesModal.payload.parcelas || []).length} itens
                      </span>
                    </div>
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-[#0f0f0f]">
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222]">Venc.</th>
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222]">Parcela</th>
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222]">Tipo</th>
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222] text-right">Valor</th>
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222] text-right">Pago</th>
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222] text-right">Desc.</th>
                          <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222] text-right">Variação</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(condicoesModal.payload.parcelas || []).map((p) => (
                          <tr key={p.id} className="border-b border-[#1f1f1f] hover:bg-[#111] text-[#ddd]">
                            <td className="p-3 font-mono text-[#bbb]">{p.data || '-'}</td>
                            <td className="p-3 font-mono text-[#888]">{p.parcela || '-'}</td>
                            <td className="p-3 font-bold">{p.forma_pagto_descricao || p.obs || '-'}</td>
                            <td className="p-3 text-right font-mono">{formatCurrency(p.valor_parcela || 0)}</td>
                            <td className={`p-3 text-right font-mono ${(p.total_pago || 0) > 0 ? 'text-[#34c759]' : 'text-[#888]'}`}>{formatCurrency(p.total_pago || 0)}</td>
                            <td className="p-3 text-right font-mono text-[#ffcc00]">{formatCurrency(p.desconto || 0)}</td>
                            <td className="p-3 text-right font-mono text-[#a259ff]">{formatCurrency(p.variacao || 0)}</td>
                          </tr>
                        ))}
                        {(condicoesModal.payload.parcelas || []).length === 0 && (
                          <tr>
                            <td colSpan="7" className="p-4 text-center text-[#666] italic">Nenhuma parcela encontrada em RECEBER para esta venda.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  {(condicoesModal.payload.distratos || []).length > 0 && (
                    <div className="bg-[#131313] border border-[#ff4d00]/30 rounded-sm overflow-hidden">
                      <div className="p-3 bg-[#0a0a0a] border-b border-[#222]">
                        <h4 className="text-[10px] uppercase tracking-widest text-[#ff4d00] font-bold">Distrato(s)</h4>
                      </div>
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-[#0f0f0f]">
                            <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222]">Data</th>
                            <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222] text-right">Valor devolvido</th>
                            <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#222]">Pagamento</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(condicoesModal.payload.distratos || []).map((d) => (
                            <tr key={d.id} className="border-b border-[#1f1f1f] hover:bg-[#111] text-[#ddd]">
                              <td className="p-3 font-mono">{d.data || '-'}</td>
                              <td className="p-3 text-right font-mono text-[#ff4d00]">{formatCurrency(d.valor_devolvido || 0)}</td>
                              <td className="p-3 font-mono">{d.data_pagamento || '-'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const RecebimentosView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [unidadeFilter, setUnidadeFilter] = useState('');
  const [clienteFilter, setClienteFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => {
        if (!Array.isArray(d)) {
           console.error("Backend error:", d);
           setData([]);
           setLoading(false);
           return;
        }
        setData(d);
        // auto select first emp if any
        const emps = [...new Set(d.map(r => r.empreendimento))].sort();
        if (emps.length > 0) {
           setEmpreendimentoFilter(emps[0]);
        } else {
           setEmpreendimentoFilter('');
        }
        setUnidadeFilter('');
        setClienteFilter('');
        setDateFrom('');
        setDateTo('');
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedEmpresa]);

  const uniqueEmps = [...new Set(data.map(r => r.empreendimento))].sort();
  const filteredBase = data.filter(r => !empreendimentoFilter || r.empreendimento === empreendimentoFilter);
  const uniqueUnidades = [...new Set(filteredBase.map(r => r.descricao_venda).filter(Boolean))].sort();
  const uniqueClientes = [...new Set(filteredBase.map(r => r.cliente).filter(Boolean))].sort();

  const inDateRange = (dateStr) => {
    // backend retorna YYYY-MM-DD (string)
    if (!dateFrom && !dateTo) return true;
    if (!dateStr || typeof dateStr !== 'string') return false;
    if (dateFrom && dateStr < dateFrom) return false;
    if (dateTo && dateStr > dateTo) return false;
    return true;
  };

  const filtered = filteredBase.filter(r =>
    inDateRange(r.data) &&
    (!unidadeFilter || r.descricao_venda === unidadeFilter) &&
    (!clienteFilter || r.cliente === clienteFilter)
  );

  useEffect(() => {
    // quando troca o empreendimento, reseta filtros específicos
    setUnidadeFilter('');
    setClienteFilter('');
    setDateFrom('');
    setDateTo('');
  }, [empreendimentoFilter]);

  const totalPago = filtered.reduce((acc, curr) => acc + ((curr.total > 0) ? curr.total : 0), 0);
  const totalParcela = filtered.reduce((acc, curr) => acc + (curr.parcela || 0), 0);
  const totalVariacao = filtered.reduce((acc, curr) => acc + (curr.variacao || 0), 0);

  const handleDarBaixa = async (r) => {
    if (!r.id) return alert("Parcela não possui ID vinculado.");
    const valorInput = prompt(`Dar baixa na parcela ${r.num_parcela} de ${formatCurrency(r.parcela)}?\nDigite o valor pago:`, r.parcela);
    if (!valorInput) return;
    const valorPago = parseFloat(valorInput.replace(',', '.'));
    if (isNaN(valorPago) || valorPago <= 0) return alert("Valor inválido");

    try {
      setLoading(true);
      await fetch(`${API_BASE}/api/vulcano/recebimentos/baixa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_receber: r.id, valor_pago: valorPago })
      });
      alert("Baixa realizada com sucesso!");
      // reload component
      fetch(`${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`)
        .then(res => res.json())
        .then(d => { setData(d); setLoading(false); });
    } catch (err) {
      alert("Erro ao dar baixa");
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tighter uppercase mb-2 text-white flex items-center gap-3"><DollarSign className="text-[#34c759]" size={28}/> Extrato de Recebimentos</h2>
          <p className="text-xs text-[#555] uppercase tracking-[0.3em]">Fluxo de Caixa Analítico por Parcela</p>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={() => {
            const csvContent = "data:text/csv;charset=utf-8," + "Data,Total_Pago,Parcela,Variacao,Venda,Cliente\n" + filtered.map(e => `${e.data},${e.total},${e.parcela},${e.variacao},"${e.descricao_venda}","${e.cliente}"`).join("\n");
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "recebimentos.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          }} className="bg-[#333] text-white text-[10px] font-bold uppercase tracking-widest px-4 py-2 rounded-sm hover:opacity-80 transition-opacity flex items-center gap-2">
            <Download size={14}/> Baixar CSV
          </button>
          <button onClick={() => setShowForm(!showForm)} className="bg-[#34c759] text-[#111] text-[10px] font-bold uppercase tracking-widest px-4 py-2 rounded-sm hover:opacity-80 transition-opacity flex items-center gap-2">
            <Plus size={14}/> Cadastrar
          </button>
        </div>
      </div>

      {showForm && (
        <div className="bg-[#131313] border border-[#34c759]/50 rounded-sm p-4 animate-in fade-in slide-in-from-top-4">
          <h3 className="text-xs uppercase tracking-widest text-[#34c759] font-bold mb-4">Novo Recebimento</h3>
          <form className="flex gap-4 items-end" onSubmit={async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            try {
              await fetch("http://localhost:8001/api/recebimentos", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(fd)) });
              alert("Recebimento cadastrado!"); e.target.reset(); setShowForm(false);
            } catch (err) { alert("Erro ao cadastrar."); }
          }}>
            <div className="w-24"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">ID Venda</label><input name="id_venda" type="number" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
            <div className="w-32"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Parcela (No)</label><input name="parcela" type="number" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
            <div className="w-32"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Valor</label><input name="valor" type="number" step="0.01" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
            <div className="w-40"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Data</label><input name="data" type="date" required className="w-full bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white" /></div>
            <button type="submit" className="bg-[#34c759] text-[#111] text-[10px] font-bold uppercase tracking-widest px-6 py-2 rounded-sm hover:opacity-80">Salvar</button>
          </form>
        </div>
      )}

      <div className="flex gap-6 h-full overflow-hidden">
        <div className="w-56 bg-[#131313] border border-[#333] rounded-sm flex flex-col shrink-0">
          <div className="p-4 border-b border-[#333] bg-[#0a0a0a]">
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-[#555]">Empreendimento</h3>
          </div>
          <div className="overflow-y-auto flex-1 p-2">
            <div 
              onClick={() => setEmpreendimentoFilter('')}
              className={`p-3 text-xs font-bold cursor-pointer transition-colors ${empreendimentoFilter === '' ? 'text-white bg-[#34c759]/10 border-l-2 border-[#34c759]' : 'text-[#888] hover:text-white hover:bg-[#1a1a1a] border-l-2 border-transparent'}`}
            >
              &lt;&lt;&lt; Consolidado Geral &gt;&gt;&gt;
            </div>
            {uniqueEmps.map((emp, i) => (
              <div 
                key={i} 
                onClick={() => setEmpreendimentoFilter(emp)}
                className={`p-3 text-xs cursor-pointer transition-colors truncate ${empreendimentoFilter === emp ? 'text-white bg-[#34c759]/10 border-l-2 border-[#34c759] font-bold' : 'text-[#888] hover:text-white hover:bg-[#1a1a1a] border-l-2 border-transparent'}`} 
                title={emp}
              >
                {emp}
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 flex flex-col gap-6 overflow-hidden">
          <div className="bg-[#131313] border border-[#333] rounded-sm p-4 shrink-0">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="min-w-[180px]">
                <label className="text-[10px] uppercase tracking-widest text-[#555] font-bold block mb-2">Data inicial</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full bg-[#0a0a0a] border border-[#333] text-white p-2 rounded-sm outline-none focus:border-[#34c759] text-xs font-bold tracking-widest uppercase transition-colors"
                />
              </div>
              <div className="min-w-[180px]">
                <label className="text-[10px] uppercase tracking-widest text-[#555] font-bold block mb-2">Data final</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full bg-[#0a0a0a] border border-[#333] text-white p-2 rounded-sm outline-none focus:border-[#34c759] text-xs font-bold tracking-widest uppercase transition-colors"
                />
              </div>
              <div className="min-w-[260px] flex-1">
                <label className="text-[10px] uppercase tracking-widest text-[#555] font-bold block mb-2">Filtrar por Unidade</label>
                <select
                  value={unidadeFilter}
                  onChange={(e) => setUnidadeFilter(e.target.value)}
                  className="w-full bg-[#0a0a0a] border border-[#333] text-white p-2 rounded-sm outline-none focus:border-[#34c759] text-xs font-bold tracking-widest uppercase transition-colors"
                >
                  <option value="">— Todas —</option>
                  {uniqueUnidades.map((u) => (
                    <option key={u} value={u}>{u}</option>
                  ))}
                </select>
              </div>
              <div className="min-w-[260px] flex-1">
                <label className="text-[10px] uppercase tracking-widest text-[#555] font-bold block mb-2">Filtrar por Cliente</label>
                <select
                  value={clienteFilter}
                  onChange={(e) => setClienteFilter(e.target.value)}
                  className="w-full bg-[#0a0a0a] border border-[#333] text-white p-2 rounded-sm outline-none focus:border-[#34c759] text-xs font-bold tracking-widest uppercase transition-colors"
                >
                  <option value="">— Todos —</option>
                  {uniqueClientes.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={() => { setDateFrom(''); setDateTo(''); setUnidadeFilter(''); setClienteFilter(''); }}
                className="bg-[#0a0a0a] border border-[#333] text-[#888] hover:text-white hover:border-[#555] px-4 py-2 rounded-sm text-[10px] font-bold uppercase tracking-widest transition-colors"
                title="Limpar filtros (data/unidade/cliente)"
              >
                Limpar
              </button>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-6 shrink-0">
            <div className="magma-card p-4 rounded-sm border-l-4 border-l-[#34c759]">
              <p className="text-[10px] uppercase tracking-widest text-[#888] font-bold mb-1">Total Recebido (Caixa)</p>
              <h4 className="text-2xl font-black text-white">{formatCurrency(totalPago)}</h4>
            </div>
            <div className="magma-card p-4 rounded-sm border-l-4 border-l-[#007aff]">
              <p className="text-[10px] uppercase tracking-widest text-[#888] font-bold mb-1">Total Valor Origin. Parcela</p>
              <h4 className="text-2xl font-black text-white">{formatCurrency(totalParcela)}</h4>
            </div>
            <div className="magma-card p-4 rounded-sm border-l-4 border-l-[#ffcc00] flex justify-between items-center">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-[#888] font-bold mb-1">Variação Acumulada</p>
                <h4 className="text-2xl font-black text-white">{formatCurrency(totalVariacao)}</h4>
              </div>
              <ArrowUpRight className="text-[#ffcc00]" size={24}/>
            </div>
          </div>

          <div className="bg-[#131313] border border-[#333] rounded-sm flex flex-col flex-1 overflow-hidden shadow-xl">
            <div className="overflow-auto flex-1 relative">
              {loading && (
                <div className="absolute inset-0 bg-[#131313]/80 backdrop-blur-sm flex flex-col items-center justify-center z-10">
                  <Loader2 className="animate-spin text-[#34c759] mb-4" size={32} />
                  <span className="text-xs font-bold uppercase tracking-widest text-[#888]">Processando Recebimentos...</span>
                </div>
              )}
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-[#0a0a0a]">
                    <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] w-24">Data Pagto</th>
                    <th className="p-3 text-[10px] tracking-widest text-[#34c759] uppercase font-bold border-b border-[#333] text-right">Total Pago</th>
                    <th className="p-3 text-[10px] tracking-widest text-[#007aff] uppercase font-bold border-b border-[#333] text-right">Valor Parcela</th>
                    <th className="p-3 text-[10px] tracking-widest text-[#ffcc00] uppercase font-bold border-b border-[#333] text-right">Variação</th>
                    <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Unidade(s) / Venda</th>
                    <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Cliente</th>
                    <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333]">Obs</th>
                    <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold border-b border-[#333] text-center w-24">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.slice(0, 500).map((r, idx) => (
                    <tr key={idx} className={`border-b border-[#222] hover:bg-[#1a1a1a] ${!r.total || r.total <= 0 ? 'bg-[#ffcc00]/5' : ''}`}>
                      <td className="p-3 text-[#ccc] whitespace-nowrap">{r.data}</td>
                      <td className="p-3 text-right font-black text-[#34c759]">{r.total > 0 ? formatCurrency(r.total) : <span className="text-[#888] text-[10px] uppercase font-bold">Aberto</span>}</td>
                      <td className="p-3 text-right font-bold text-[#007aff]">{formatCurrency(r.parcela)}</td>
                      <td className="p-3 text-right font-bold text-[#ffcc00]">{formatCurrency(r.variacao)}</td>
                      <td className="p-3 text-xs text-[#888] truncate max-w-[200px]" title={r.descricao_venda}>
                        {r.descricao_venda}
                      </td>
                      <td className="p-3 text-xs text-[#ccc] truncate max-w-[150px]">{r.cliente}</td>
                      <td className="p-3 text-[10px] uppercase tracking-widest text-[#888] font-bold truncate max-w-[100px]">{r.obs}</td>
                      <td className="p-3 text-center">
                        {(!r.total || r.total <= 0) ? (
                            <button onClick={() => handleDarBaixa(r)} className="bg-[#34c759]/20 text-[#34c759] hover:bg-[#34c759] hover:text-white transition-colors text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded">
                              Baixar
                            </button>
                        ) : (
                            <span className="text-[#34c759] text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-1"><CheckCircle size={12}/> Pago</span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {!loading && filtered.length > 500 && (
                    <tr>
                      <td colSpan="8" className="p-4 text-center text-[#ffcc00] text-xs font-bold uppercase tracking-widest">Exibindo 500 últimos registros. Filtre para ver mais.</td>
                    </tr>
                  )}
                  {!loading && filtered.length === 0 && (
                    <tr>
                      <td colSpan="8" className="p-8 text-center text-[#555] italic">Nenhum recebimento registrado para este filtro.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const ConciliadorView = ({ selectedEmpresa }) => {
  const [pdfFile, setPdfFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [hasCode, setHasCode] = useState(false);
  const [codePreview, setCodePreview] = useState('');
  const [codeStats, setCodeStats] = useState({ chars: 0, lines: 0 });
  const fullCodeRef = React.useRef('');
  const [templateNome, setTemplateNome] = useState('');
  const [templateDescricao, setTemplateDescricao] = useState('');
  const [definirPadrao, setDefinirPadrao] = useState(true);
  const [savedTemplates, setSavedTemplates] = useState([]);
  const [pickTemplateId, setPickTemplateId] = useState('');
  const [lastTemplateId, setLastTemplateId] = useState(null);
  /** Se true, ignora modelo/padrão e chama só o Gemini na extração. */
  const [extractForceAi, setExtractForceAi] = useState(false);

  const [extractedData, setExtractedData] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  const fileInputRef = React.useRef(null);

  const applyCodeToPreview = (raw) => {
    const code = typeof raw === 'string' ? raw : '';
    fullCodeRef.current = code;
    const lines = code ? code.split('\n').length : 0;
    const maxPreview = 14000;
    if (code.length > maxPreview) {
      setCodePreview(
        code.slice(0, maxPreview) +
          `\n\n# … ${code.length - maxPreview} caracteres omitidos na tela (use Baixar .py para o arquivo completo).`
      );
    } else {
      setCodePreview(code);
    }
    setCodeStats({ chars: code.length, lines });
    setHasCode(!!code.trim());
  };

  const resetSession = () => {
    setPdfFile(null);
    setExtractedData([]);
    setChatHistory([]);
    setChatInput('');
    setHasCode(false);
    setCodePreview('');
    setCodeStats({ chars: 0, lines: 0 });
    fullCodeRef.current = '';
    setTemplateNome('');
    setTemplateDescricao('');
    setLastTemplateId(null);
    setPickTemplateId('');
    setExtractForceAi(false);
    setErrorMsg('');
  };

  const fetchTemplates = () => {
    const q = selectedEmpresa ? `?empresa_id=${encodeURIComponent(selectedEmpresa)}` : '';
    fetch(`${API_BASE}/api/parser/templates${q}`)
      .then((r) => r.json())
      .then((d) => setSavedTemplates(Array.isArray(d) ? d : []))
      .catch(() => setSavedTemplates([]));
  };

  useEffect(() => {
    fetchTemplates();
  }, [selectedEmpresa]);

  const handleLoadSavedTemplate = async () => {
    const id = pickTemplateId;
    if (!id) {
      alert('Selecione um modelo na lista.');
      return;
    }
    setErrorMsg('');
    try {
      const res = await fetch(`${API_BASE}/api/parser/templates/${encodeURIComponent(id)}`);
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
      const code = typeof json.python_code === 'string' ? json.python_code : '';
      applyCodeToPreview(code);
      if (json.nome) setTemplateNome(json.nome);
      if (json.descricao != null) setTemplateDescricao(json.descricao || '');
      if (json.id != null) setLastTemplateId(json.id);
    } catch (e) {
      console.error(e);
      setErrorMsg(e.message || 'Falha ao carregar modelo.');
    }
  };

  const handleSetPadraoLista = async () => {
    if (!selectedEmpresa || !pickTemplateId) {
      alert('Selecione empresa (topo) e um modelo na lista.');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/parser/templates/set-default`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empresa_id: parseInt(selectedEmpresa, 10),
          parser_template_id: parseInt(pickTemplateId, 10),
        }),
      });
      if (!res.ok) throw new Error('Falha');
      fetchTemplates();
      alert('Modelo definido como padrão desta empresa.');
    } catch {
      alert('Não foi possível definir o padrão.');
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setPdfFile(f);
      setExtractedData([]);
      setChatHistory([]);
      setChatInput('');
      setErrorMsg('');
      setHasCode(false);
      setCodePreview('');
      fullCodeRef.current = '';
      setTemplateNome(f.name.replace(/\.pdf$/i, '').replace(/\.pdf\.pdf$/i, '') || '');
    }
  };

  const withTimeout = async (fn, ms, timeoutMessage) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), ms);
    try {
      return await fn(controller.signal);
    } catch (e) {
      if (e?.name === 'AbortError') throw new Error(timeoutMessage || 'Tempo limite excedido.');
      throw e;
    } finally {
      clearTimeout(id);
    }
  };

  const handleExtract = async () => {
    if (!pdfFile) return;
    setIsProcessing(true);
    setHasCode(false);
    setCodePreview('');
    fullCodeRef.current = '';
    setLastTemplateId(null);
    setExtractedData([]);
    setChatHistory([]);
    setChatInput('');
    setErrorMsg('');

    const formData = new FormData();
    formData.append('file', pdfFile);
    const qs = new URLSearchParams();
    if (!extractForceAi) {
      if (pickTemplateId) {
        qs.set('parser_template_id', String(pickTemplateId));
      } else if (selectedEmpresa) {
        qs.set('empresa_id', String(selectedEmpresa));
      }
    }
    const extractUrl = `${API_BASE}/api/extract-pdf${qs.toString() ? `?${qs.toString()}` : ''}`;

    try {
      const data = await withTimeout(async (signal) => {
        const res = await fetch(extractUrl, { method: 'POST', body: formData, signal });
        const text = await res.text();
        let json = {};
        try {
          json = text ? JSON.parse(text) : {};
        } catch {
          throw new Error(
            res.ok
              ? `Resposta inválida do servidor (não é JSON). Trecho: ${text.slice(0, 240)}`
              : `Erro HTTP ${res.status}: ${text.slice(0, 400)}`
          );
        }
        if (!res.ok) {
          const d = json.detail;
          const msg = Array.isArray(d)
            ? d.map((x) => (typeof x === 'string' ? x : x.msg || JSON.stringify(x))).join('; ')
            : typeof d === 'string'
              ? d
              : d != null
                ? JSON.stringify(d)
                : '';
          throw new Error(msg || `Erro HTTP ${res.status}`);
        }
        return json;
      }, 180000, 'A extração demorou demais (3 min). Parser, IA ou rede — veja o terminal do uvicorn.');

      const rows = Array.isArray(data.extracted_data) ? data.extracted_data : [];
      setExtractedData(rows);
      const via =
        data.parser_source === 'template'
          ? `Script salvo (#${data.parser_template_id ?? pickTemplateId ?? '—'}), sem IA.`
          : data.parser_source === 'gemini_fallback'
            ? `Gemini (fallback do modelo #${data.parser_template_id ?? pickTemplateId ?? '—'})`
            : 'Gemini (IA).';
      const hintZero =
        rows.length === 0 && data.parser_source === 'template'
          ? ' Nenhuma linha: o regex do modelo pode não bater com este PDF (ou resposta inválida). Tente “Só IA” para comparar.'
          : '';
      if (rows.length === 0 && (data.parser_source === 'gemini' || data.parser_source === 'gemini_fallback')) {
        setErrorMsg('A IA não encontrou linhas neste PDF. Pode ser outro tipo de relatório (o prompt atual busca recebimentos) ou o texto extraído está diferente do esperado.');
      }
      if (rows.length === 0 && data.parser_source === 'template') {
        setErrorMsg('O modelo salvo rodou, mas não encontrou linhas. Provável: este PDF não segue o mesmo layout do modelo ou o regex do script não casou.');
      }
      setChatHistory([
        { role: 'assistant', content: `Extração concluída (${via}) Linhas: ${rows.length}.${hintZero}` },
      ]);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'Falha ao extrair PDF.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleChatAdjust = async () => {
    const instruction = chatInput.trim();
    if (!instruction) return;
    if (!Array.isArray(extractedData)) return;
    setIsChatting(true);
    setErrorMsg('');

    const historyNext = [...chatHistory, { role: 'user', content: instruction }];
    setChatHistory(historyNext);
    setChatInput('');

    try {
      const resp = await withTimeout(async (signal) => {
        const res = await fetch(`${API_BASE}/api/parser/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ instruction, current_data: extractedData }),
          signal
        });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
        return json;
      }, 180000, 'O chat demorou demais (3 min). Verifique GEMINI_API_KEY e a conexão.');

      const updated = Array.isArray(resp.updated_data) ? resp.updated_data : extractedData;
      setExtractedData(updated);
      setChatHistory(prev => [...prev, { role: 'assistant', content: resp.message || `Aplicado ajuste. Linhas atuais: ${updated.length}.` }]);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'Falha ao ajustar via chat.');
      setChatHistory(prev => [...prev, { role: 'assistant', content: `Erro: ${err.message || 'falha no ajuste'}` }]);
    } finally {
      setIsChatting(false);
    }
  };

  const handleGeneratePython = async () => {
    if (!Array.isArray(extractedData) || extractedData.length === 0) return;
    const nome = (templateNome || '').trim() || (pdfFile?.name?.replace(/\.pdf$/i, '') || 'Parser PDF');
    setIsSaving(true);
    setErrorMsg('');
    setHasCode(false);
    setCodePreview('');
    fullCodeRef.current = '';

    try {
      const resp = await withTimeout(async (signal) => {
        const res = await fetch(`${API_BASE}/api/parser/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            history: chatHistory,
            final_data: extractedData,
            nome,
            descricao: templateDescricao || null,
            empresa_id: selectedEmpresa ? parseInt(selectedEmpresa, 10) : null,
            definir_padrao_empresa: definirPadrao && !!selectedEmpresa,
          }),
          signal
        });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
        return json;
      }, 300000, 'A geração do script demorou demais (5 min). Verifique GEMINI_API_KEY e a conexão.');

      const raw =
        (resp.code && typeof resp.code === 'string' && resp.code) ||
        (resp.python_code && typeof resp.python_code === 'string' && resp.python_code) ||
        `# ${resp.status || 'Script'}\n# ${resp.filename || ''}\n`;
      applyCodeToPreview(raw);
      if (resp.template_id != null) {
        setLastTemplateId(resp.template_id);
        setPickTemplateId(String(resp.template_id));
      }
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            (resp.status || 'Script gerado.') +
            (resp.template_id ? ` Registro #${resp.template_id} no sistema.` : ''),
        },
      ]);
      fetchTemplates();
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'Falha ao gerar o script.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadCode = () => {
    const full = fullCodeRef.current;
    if (!full) return;
    const blob = new Blob([full], { type: 'text/x-python' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `${(templateNome || "pdf_parser").replace(/[^\w\-]+/g, "_")}.py`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Importante: se o backend retornar 0 linhas, ainda mostramos a área de trabalho
  // para o operador ver o feedback (chat/erro) e ajustar o fluxo.
  const showWorkingView =
    isProcessing ||
    extractedData.length > 0 ||
    hasCode ||
    chatHistory.length > 0 ||
    !!errorMsg;

  const extractOverlay =
    extractForceAi || (!pickTemplateId && !selectedEmpresa)
      ? {
          title: 'Extração com IA',
          subtitle: 'Contatando a API Gemini e estruturando os valores…',
        }
      : pickTemplateId
        ? {
            title: 'Extração com modelo salvo',
            subtitle: 'Executando o script Python no backend (sem Gemini)…',
          }
        : {
            title: 'Extração',
            subtitle:
              'Se a empresa tiver parser padrão, roda o script; senão, usa a IA…',
          };

  return (
    <div className="space-y-6 animate-in fade-in max-w-[1600px] mx-auto w-full h-full flex flex-col pb-4">
      <div className="flex flex-wrap gap-4 justify-between items-end shrink-0">
        <div>
          <h2 className="text-3xl font-bold tracking-tighter text-white uppercase flex items-center gap-3">
            <Zap className="text-[#a259ff]" size={36} /> Universal PDF <span className="text-[#007aff]">Generator</span>
          </h2>
          <p className="text-sm text-[#888] mt-2 uppercase tracking-widest font-bold">Extraia valores do PDF, ajuste no chat e gere um script Python reutilizável.</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center justify-end">
          {hasCode && (
            <button
              type="button"
              onClick={handleDownloadCode}
              className="bg-[#1a1a1c] border border-[#007aff]/50 text-[#007aff] hover:bg-[#007aff] hover:text-white py-2 px-6 rounded-sm font-bold uppercase tracking-widest text-[10px] transition-colors flex items-center gap-2"
            >
              <Download size={14} /> Baixar .py
            </button>
          )}
          {showWorkingView && (
            <button
              type="button"
              onClick={resetSession}
              className="bg-[#131313] border border-[#333] text-[#888] hover:text-white hover:border-[#555] py-2 px-4 rounded-sm font-bold uppercase tracking-widest text-[10px] transition-colors"
            >
              Novo PDF
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 items-center bg-[#131313] border border-[#333] p-3 rounded-sm">
        <span className="text-[10px] font-bold uppercase tracking-widest text-[#555]">Modelos salvos</span>
        <select
          value={pickTemplateId}
          onChange={(e) => setPickTemplateId(e.target.value)}
          className="bg-[#0a0a0a] border border-[#333] text-xs text-white px-2 py-2 rounded-sm min-w-[200px] outline-none focus:border-[#007aff]"
        >
          <option value="">— selecione —</option>
          {savedTemplates.map((t) => (
            <option key={t.id} value={String(t.id)}>
              {t.nome || `Modelo #${t.id}`}
              {t.is_padrao_empresa ? ' ★' : ''}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleLoadSavedTemplate}
          disabled={!pickTemplateId}
          className="bg-[#1a1a1c] border border-[#a259ff]/40 text-[#a259ff] hover:bg-[#a259ff] hover:text-black py-2 px-4 rounded-sm font-bold uppercase tracking-widest text-[10px] disabled:opacity-50 transition-colors"
        >
          Carregar código
        </button>
        <button
          type="button"
          onClick={handleSetPadraoLista}
          disabled={!selectedEmpresa || !pickTemplateId}
          className="bg-[#1a1a1c] border border-[#34c759]/40 text-[#34c759] hover:bg-[#34c759] hover:text-black py-2 px-4 rounded-sm font-bold uppercase tracking-widest text-[10px] disabled:opacity-50 transition-colors"
          title="Marca o modelo escolhido como padrão da empresa selecionada no topo do app"
        >
          Definir padrão empresa
        </button>
      </div>

      {errorMsg && (
        <div className="bg-[#131313] border border-[#ff4d00]/50 p-4 rounded-sm text-[#ff4d00] text-xs font-bold uppercase tracking-widest">
          {errorMsg}
        </div>
      )}

      {!showWorkingView ? (
        <div className="bg-[#131313] border border-[#333] p-8 rounded-sm text-center max-w-2xl mx-auto w-full mt-10 shadow-xl">
          <FileText size={64} className="mx-auto text-[#007aff] mb-6" />
          <h3 className="text-xl font-bold text-white mb-2 uppercase tracking-widest">Extrator + Chat de Ajuste</h3>
          <p className="text-[#888] text-sm mb-8">Envie o PDF. O sistema extrai os valores, você corrige via chat e depois gera um `.py` para reutilizar nas próximas importações.</p>
          
          <div className="max-w-md mx-auto flex flex-col gap-4">
            <input 
              type="file" 
              accept=".pdf"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
            />
            <button
               onClick={() => fileInputRef.current.click()}
               className="w-full bg-[#0a0a0a] border border-[#333] hover:border-[#007aff] text-white py-4 rounded-sm font-bold uppercase tracking-widest text-xs transition-colors flex justify-center items-center gap-2"
            >
              <UploadCloud size={16} /> {pdfFile ? pdfFile.name : 'Selecionar Arquivo de Layout PDF'}
            </button>
            <label className="flex items-center gap-2 text-[10px] uppercase tracking-widest font-bold text-[#888] cursor-pointer select-none justify-center">
              <input
                type="checkbox"
                checked={extractForceAi}
                onChange={(e) => setExtractForceAi(e.target.checked)}
                className="accent-[#007aff]"
              />
              Só IA (ignorar modelo / padrão da empresa)
            </label>
            <p className="text-[10px] text-[#666] text-center leading-relaxed max-w-md mx-auto">
              Com modelo na barra acima (ou padrão da empresa no topo), a extração roda o Python salvo — sem Gemini.
            </p>
            <button 
              onClick={handleExtract}
              disabled={isProcessing || !pdfFile} 
              className="w-full bg-[#007aff] text-white py-4 rounded-sm font-bold uppercase tracking-widest text-[10px] hover:bg-[#005bb5] transition-colors disabled:opacity-50 flex justify-center items-center gap-2 shadow-[0_0_10px_rgba(0,122,255,0.4)]"
            >
              {isProcessing ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
              {isProcessing ? 'Extraindo...' : extractForceAi ? 'Extrair com IA (Gemini)' : 'Extrair PDF'}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col flex-1 overflow-hidden relative">
          {isProcessing && (
            <div className="absolute inset-0 bg-[#0a0a0a]/80 backdrop-blur-md flex flex-col items-center justify-center z-10 rounded-sm border border-[#333]">
              <Loader2 className="animate-spin text-[#007aff] mb-6" size={48} />
              <h3 className="text-xl font-bold uppercase tracking-widest text-white mb-2">{extractOverlay.title}</h3>
              <p className="text-sm font-bold text-[#aaa] tracking-wide text-center max-w-md px-4 leading-relaxed">
                {extractOverlay.subtitle}
              </p>
            </div>
          )}

          {extractedData.length > 0 && (
            <div className="grid grid-cols-12 gap-6 flex-1 overflow-hidden min-h-[280px]">
              <div className="col-span-8 bg-[#131313] border border-[#333] rounded-sm flex flex-col overflow-hidden shadow-xl">
                <div className="p-4 bg-[#1a1a1c] border-b border-[#333] space-y-3">
                  <div className="flex flex-wrap gap-3">
                    <input
                      value={templateNome}
                      onChange={(e) => setTemplateNome(e.target.value)}
                      placeholder="Nome do modelo (ex.: Fatura Fornecedor X)"
                      className="flex-1 min-w-[160px] bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white outline-none focus:border-[#ffcc00]"
                    />
                    <input
                      value={templateDescricao}
                      onChange={(e) => setTemplateDescricao(e.target.value)}
                      placeholder="Descrição (opcional)"
                      className="flex-1 min-w-[160px] bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white outline-none focus:border-[#ffcc00]"
                    />
                  </div>
                  {selectedEmpresa && (
                    <label className="flex items-center gap-2 text-[10px] uppercase tracking-widest font-bold text-[#888] cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={definirPadrao}
                        onChange={(e) => setDefinirPadrao(e.target.checked)}
                        className="accent-[#34c759]"
                      />
                      Definir como padrão desta empresa ao gerar .py
                    </label>
                  )}
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <Database size={18} className="text-[#ffcc00]" />
                      <h3 className="text-xs font-bold text-white uppercase tracking-widest leading-none">Valores Extraídos</h3>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] uppercase tracking-widest font-bold text-[#555]">{extractedData.length} linhas</span>
                      <button
                        onClick={handleGeneratePython}
                        disabled={isSaving}
                        className="bg-[#1a1a1c] border border-[#34c759]/40 text-[#34c759] hover:bg-[#34c759] hover:text-black px-4 py-2 rounded-sm font-bold uppercase tracking-widest text-[10px] transition-colors flex items-center gap-2 disabled:opacity-60"
                        title="Gera script .py, grava no disco do servidor e registra na tabela de modelos"
                      >
                        {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                        {isSaving ? 'Gerando...' : hasCode ? 'Gerar .py novamente' : 'Gerar .py'}
                      </button>
                    </div>
                  </div>
                </div>
                <div className="flex-1 overflow-auto p-4 bg-black custom-scrollbar">
                  <pre className="text-[11px] font-mono text-[#e5e2e1] leading-relaxed">
                    <code>{JSON.stringify(extractedData.slice(0, 200), null, 2)}</code>
                  </pre>
                  {extractedData.length > 200 && (
                    <div className="mt-4 text-[10px] uppercase tracking-widest font-bold text-[#555]">
                      Mostrando apenas 200 primeiras linhas (para não travar o navegador).
                    </div>
                  )}
                </div>
              </div>

              <div className="col-span-4 bg-[#131313] border border-[#333] rounded-sm flex flex-col overflow-hidden shadow-xl">
                <div className="p-4 bg-[#1a1a1c] border-b border-[#333] flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <MessageSquare size={18} className="text-[#a259ff]" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-widest leading-none">Chat de Ajustes</h3>
                  </div>
                  <div className="text-[10px] uppercase tracking-widest font-bold text-[#555]">
                    {isChatting ? 'processando...' : 'pronto'}
                  </div>
                </div>

                <div className="flex-1 overflow-auto p-4 bg-[#0a0a0a] custom-scrollbar space-y-3">
                  {chatHistory.map((m, idx) => (
                    <div key={idx} className={`text-xs leading-relaxed ${m.role === 'user' ? 'text-white' : 'text-[#888]'}`}>
                      <span className={`text-[10px] font-bold uppercase tracking-widest ${m.role === 'user' ? 'text-[#ffcc00]' : 'text-[#a259ff]'}`}>
                        {m.role === 'user' ? 'Você' : 'IA'}
                      </span>
                      <div className="mt-1 whitespace-pre-wrap break-words">{m.content}</div>
                    </div>
                  ))}
                  {chatHistory.length === 0 && (
                    <div className="text-[10px] uppercase tracking-widest font-bold text-[#555]">
                      Ex.: “Remover linhas sem data”, “Corrigir parcela 01/10A para 01/10”, “Trocar vírgula por ponto em valor_parcela”.
                    </div>
                  )}
                </div>

                <div className="p-4 border-t border-[#333] bg-[#111]">
                  <div className="flex gap-2">
                    <input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleChatAdjust(); } }}
                      placeholder="Diga como corrigir os dados..."
                      className="flex-1 bg-[#0a0a0a] border border-[#333] p-2 text-xs text-white outline-none focus:border-[#a259ff]"
                      disabled={isChatting}
                    />
                    <button
                      onClick={handleChatAdjust}
                      disabled={isChatting || !chatInput.trim()}
                      className="bg-[#a259ff] text-black px-3 py-2 rounded-sm font-bold uppercase tracking-widest text-[10px] disabled:opacity-60 flex items-center gap-2"
                    >
                      {isChatting ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                      Enviar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {hasCode && (
            <div className="bg-[#111] border border-[#333] rounded-sm flex flex-col shadow-xl overflow-hidden mt-4 max-h-[min(480px,50vh)]">
               <div className="p-4 bg-[#1a1a1c] border-b border-[#333] flex flex-wrap items-center justify-between gap-2 shadow-xl z-10">
                 <div className="flex items-center gap-3">
                   <Code size={18} className="text-[#34c759]" />
                   <h3 className="text-xs font-bold text-white uppercase tracking-widest leading-none">Script gerado (preview)</h3>
                 </div>
                 <div className="text-[10px] uppercase font-bold tracking-widest text-[#555] flex flex-wrap items-center gap-2">
                   <CheckCircle2 size={14} className="text-[#34c759]" />
                   {lastTemplateId != null && <span>Registro #{lastTemplateId}</span>}
                   <span>{codeStats.lines} linhas · {codeStats.chars.toLocaleString('pt-BR')} caracteres</span>
                 </div>
               </div>
               <div className="flex-1 overflow-auto p-6 custom-scrollbar bg-black min-h-0">
                 <pre className="text-[11px] font-mono text-[#a259ff] leading-relaxed whitespace-pre-wrap break-words">
                   <code>{codePreview}</code>
                 </pre>
               </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

