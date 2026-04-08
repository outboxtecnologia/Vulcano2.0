import React, { useState, useEffect } from 'react';
import { 
  Building2, Plus, Edit, Trash2, Search, X, Check, Loader2, 
  Settings, Database, Construction, Layers, Home, Ruler,
  ChevronRight, ArrowRight, Save, Info, AlertCircle
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:6000";

export const EmpreendimentosView = ({ selectedEmpresa }) => {
  const [empreendimentos, setEmpreendimentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingEmp, setEditingEmp] = useState(null);
  const [activeTab, setActiveTab] = useState('dados'); // 'dados', 'questor', 'estrutura'

  // Questor data for selectors
  const [planoContas, setPlanoContas] = useState([]);
  const [centrosCusto, setCentrosCusto] = useState([]);
  const [historicos, setHistoricos] = useState([]);
  const [loadingQuestor, setLoadingQuestor] = useState(false);

  // Blocos/Unidades for editing
  const [blocos, setBlocos] = useState([]);
  const [unidades, setUnidades] = useState([]);
  const [loadingEstrutura, setLoadingEstrutura] = useState(false);
  const [newBlocoName, setNewBlocoName] = useState('');
  const [newUnidade, setNewUnidade] = useState({ id_bloco: '', descricao: '', metragem: '', inscricao: '' });

  const [formData, setFormData] = useState({
    nome: '',
    cnpj: '',
    cno: '',
    metragem: 0,
    custo: 0,
    endereco: '',
    ret: 'N',
    ativo: 'S',
    data_conclusao: '',
    conta_caixa: 0,
    conta_clientes: 0,
    conta_adi_cli: 0,
    conta_estand: 0,
    conta_estcon: 0,
    conta_despesa: 0,
    conta_rec: 0,
    conta_variacao: 0,
    conta_devolucao: 0,
    centro_custo: 0,
    hist_venda: 0,
    hist_recebimento: 0,
    hist_variacao: 0,
    hist_distrato: 0,
    hist_estorno: 0
  });

  useEffect(() => {
    fetchEmpreendimentos();
    if (selectedEmpresa) {
        fetchQuestorData();
    }
  }, [selectedEmpresa]);

  const fetchEmpreendimentos = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`);
      const data = await res.json();
      setEmpreendimentos(data);
      setLoading(false);
    } catch (err) {
      setError("Falha ao comunicar com node Vulcano");
      setLoading(false);
    }
  };

  const fetchQuestorData = async () => {
    setLoadingQuestor(true);
    try {
        const [pc, cc, hi] = await Promise.all([
            fetch(`${API_BASE}/api/questor/plano-contas-espec?empresa_id=${selectedEmpresa}`).then(r => r.json()),
            fetch(`${API_BASE}/api/questor/centrocusto`).then(r => r.json()),
            fetch(`${API_BASE}/api/questor/historicos`).then(r => r.json())
        ]);
        setPlanoContas(pc.contas || []);
        setCentrosCusto(cc || []);
        setHistoricos(hi || []);
    } catch (e) {
        console.error("Erro Questor Mapping:", e);
    } finally {
        setLoadingQuestor(false);
    }
  };

  const fetchEstrutura = async (empId) => {
    setLoadingEstrutura(true);
    try {
        const res = await fetch(`${API_BASE}/api/vulcano/empreendimentos/${empId}/detalhes`);
        const data = await res.json();
        setBlocos(data.blocos || []);
        setUnidades(data.unidades || []);
    } catch (e) {
        console.error("Erro Estrutura:", e);
    } finally {
        setLoadingEstrutura(false);
    }
  };

  const handleOpenModal = (emp = null) => {
    if (emp) {
      setEditingEmp(emp);
      setFormData({
        ...emp,
        ret: emp.ret || 'N',
        ativo: emp.ativo || 'S'
      });
      fetchEstrutura(emp.id);
    } else {
      setEditingEmp(null);
      setFormData({
        nome: '', cnpj: '', cno: '', metragem: 0, custo: 0, endereco: '',
        ret: 'N', ativo: 'S', data_conclusao: '',
        conta_caixa: 0, conta_clientes: 0, conta_adi_cli: 0,
        conta_estand: 0, conta_estcon: 0, conta_despesa: 0, conta_rec: 0, 
        conta_variacao: 0, conta_devolucao: 0, centro_custo: 0,
        hist_venda: 0, hist_recebimento: 0, hist_variacao: 0, hist_distrato: 0, hist_estorno: 0
      });
      setBlocos([]);
      setUnidades([]);
    }
    setActiveTab('dados');
    setShowModal(true);
  };

  const handleSave = async () => {
    const method = editingEmp ? 'PATCH' : 'POST';
    const url = editingEmp 
      ? `${API_BASE}/api/vulcano/empreendimentos/${editingEmp.id}`
      : `${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`;
    
    // Ensure numeric fields are correctly typed
    const payload = {
        ...formData,
        empresa_id: parseInt(selectedEmpresa),
        metragem: parseFloat(formData.metragem || 0),
        custo: parseFloat(formData.custo || 0),
        conta_caixa: parseInt(formData.conta_caixa || 0),
        conta_clientes: parseInt(formData.conta_clientes || 0),
        conta_adi_cli: parseInt(formData.conta_adi_cli || 0),
        conta_estand: parseInt(formData.conta_estand || 0),
        conta_estcon: parseInt(formData.conta_estcon || 0),
        conta_despesa: parseInt(formData.conta_despesa || 0),
        conta_rec: parseInt(formData.conta_rec || 0),
        conta_variacao: parseInt(formData.conta_variacao || 0),
        conta_devolucao: parseInt(formData.conta_devolucao || 0),
        centro_custo: parseInt(formData.centro_custo || 0),
        hist_venda: parseInt(formData.hist_venda || 0),
        hist_recebimento: parseInt(formData.hist_recebimento || 0),
        hist_variacao: parseInt(formData.hist_variacao || 0),
        hist_distrato: parseInt(formData.hist_distrato || 0),
        hist_estorno: parseInt(formData.hist_estorno || 0)
    };

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowModal(false);
        fetchEmpreendimentos();
      } else {
        const errData = await res.json();
        alert("Erro ao salvar: " + JSON.stringify(errData.detail));
      }
    } catch (err) {
      alert("Erro de rede");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Tem certeza que deseja remover permanentemente este empreendimento e toda sua estrutura (Blocos/Unidades)?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/empreendimentos/${id}`, { method: 'DELETE' });
      if (res.ok) fetchEmpreendimentos();
    } catch (err) {
      alert("Erro ao deletar");
    }
  };

  // Blocos/Unidades Management
  const handleAddBloco = async () => {
    if (!newBlocoName.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/blocos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_empreendimento: editingEmp.id, nome: newBlocoName })
      });
      if (res.ok) {
        setNewBlocoName('');
        fetchEstrutura(editingEmp.id);
      }
    } catch (e) { alert("Erro ao criar bloco"); }
  };

  const handleAddUnidade = async () => {
    if (!newUnidade.id_bloco || !newUnidade.descricao) return;
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/unidades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUnidade)
      });
      if (res.ok) {
        setNewUnidade({ ...newUnidade, descricao: '', metragem: '', inscricao: '' });
        fetchEstrutura(editingEmp.id);
      }
    } catch (e) { alert("Erro ao criar unidade"); }
  };

  const handleDeleteEstrutura = async (type, id) => {
    const url = type === 'bloco' ? `${API_BASE}/api/vulcano/blocos/${id}` : `${API_BASE}/api/vulcano/unidades/${id}`;
    if (confirm(`Remover ${type === 'bloco' ? 'BLOCO e todas as suas unidades' : 'UNIDADE'}?`)) {
        await fetch(url, { method: 'DELETE' });
        fetchEstrutura(editingEmp.id);
    }
  };

  // Filtered account selectors helper
  const renderAccountInput = (label, name, prefix) => {
    const filtered = planoContas.filter(c => c.classificacao.startsWith(prefix));
    const listId = `list-${name}`;
    return (
      <div className="space-y-1">
        <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">{label}</label>
        <div className="relative group">
            <input
                list={listId}
                value={formData[name] || ''}
                onChange={(e) => setFormData({ ...formData, [name]: e.target.value })}
                className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50 transition-all font-mono"
                placeholder={loadingQuestor ? "Carregando..." : "Digite ou selecione..."}
            />
            <datalist id={listId}>
                {filtered.map(c => (
                    <option key={c.id} value={c.id}>{c.classificacao} - {c.descricao}</option>
                ))}
            </datalist>
            <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-20 group-hover:opacity-100 transition-opacity">
                <Search size={12} className="text-[#ff4d00]" />
            </div>
        </div>
        <p className="text-[9px] text-[#444] font-medium">Questor ID: {formData[name] || '0'}</p>
      </div>
    );
  };

  if (loading && !empreendimentos.length) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-20 gap-4">
        <Loader2 className="animate-spin text-[#ff4d00]" size={40} />
        <span className="text-[10px] font-black uppercase tracking-widest text-[#555]">Mapeando Infraestruturas...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex justify-between items-end border-b border-white/5 pb-6">
        <div>
          <h2 className="font-headline text-3xl font-black tracking-tight text-white uppercase italic">Central de Empreendimentos</h2>
          <p className="text-[10px] text-[#ff4d00] font-black uppercase tracking-[0.4em] mt-1">Gestão de Nodes & Infraestrutura Vulcano</p>
        </div>
        <button 
          onClick={() => handleOpenModal()}
          className="bg-[#ff4d00] text-black px-6 py-3 rounded-sm font-black text-[10px] uppercase tracking-[0.2em] flex items-center gap-2 hover:bg-white transition-all shadow-[0_0_20px_rgba(255,77,0,0.3)] group"
        >
          <Plus size={16} className="group-hover:rotate-90 transition-transform" /> Novo Empreendimento
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {empreendimentos.map(emp => (
          <div key={emp.id} className="group relative">
            <div className="p-6 bg-black/40 backdrop-blur-md border border-white/5 rounded-sm hover:border-[#ff4d00]/30 transition-all duration-300 flex flex-col h-full gap-4">
              <div className="flex justify-between items-start">
                <div className="w-10 h-10 bg-white/5 flex items-center justify-center rounded-sm">
                  <Building2 size={20} className={emp.ativo === 'N' ? "text-[#34c759]" : "text-[#ff4d00]"} />
                </div>
                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => handleOpenModal(emp)} className="p-2 bg-white/5 hover:bg-[#ff4d00]/10 hover:text-[#ff4d00] rounded-sm transition-colors"><Edit size={14}/></button>
                  <button onClick={() => handleDelete(emp.id)} className="p-2 bg-white/5 hover:bg-[#ff3b30]/10 hover:text-[#ff3b30] rounded-sm transition-colors"><Trash2 size={14}/></button>
                </div>
              </div>
              
              <div className="space-y-1">
                <h3 className="font-headline font-black text-white uppercase tracking-wider text-sm">{emp.nome}</h3>
                <p className="text-[10px] text-[#555] font-bold uppercase py-1 border-b border-white/5">CNO: {emp.cno || 'Não Informado'}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-2">
                <div className="space-y-1">
                  <span className="text-[9px] text-[#444] font-black uppercase tracking-widest block">Metragem</span>
                  <div className="flex items-center gap-1.5 text-white/80 font-mono text-[11px]">
                    <Ruler size={12} className="text-[#ff4d00]" /> {emp.metragem || 0} m²
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-[9px] text-[#444] font-black uppercase tracking-widest block">Custo Orc.</span>
                  <div className="flex items-center gap-1.5 text-white/80 font-mono text-[11px]">
                    <Database size={12} className="text-[#34c759]" /> {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(emp.custo || 0)}
                  </div>
                </div>
              </div>

              <div className="mt-auto pt-4 flex items-center justify-between">
                 <div className="flex gap-2">
                    {emp.ret === 'S' && <span className="text-[8px] bg-[#ff4d00]/10 text-[#ff4d00] border border-[#ff4d00]/20 px-1.5 py-0.5 rounded-sm font-black uppercase">RET</span>}
                    {emp.ativo === 'N' ? 
                       <span className="text-[8px] bg-[#34c759]/10 text-[#34c759] border border-[#34c759]/20 px-1.5 py-0.5 rounded-sm font-black uppercase">Concluído</span> :
                       <span className="text-[8px] bg-[#007aff]/10 text-[#007aff] border border-[#007aff]/20 px-1.5 py-0.5 rounded-sm font-black uppercase">Em Obras</span>
                    }
                 </div>
                 <div className="text-[9px] font-black text-[#555] uppercase tracking-widest">ID {emp.id}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/90 backdrop-blur-sm" onClick={() => setShowModal(false)}></div>
          <div className="relative w-full max-w-4xl bg-[#0a0a0a] border border-white/10 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
            
            {/* Header Modal */}
            <div className="p-6 border-b border-white/5 flex justify-between items-center bg-black/40">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-[#ff4d00] text-black flex items-center justify-center rounded-sm">
                  <Building2 size={24} />
                </div>
                <div>
                  <h3 className="font-headline text-xl font-black text-white uppercase tracking-tight">
                    {editingEmp ? 'Editar Empreendimento' : 'Novo Empreendimento'}
                  </h3>
                  <p className="text-[10px] text-[#555] font-black uppercase tracking-widest">Configuração de Parâmetros e Mapeamento</p>
                </div>
              </div>
              <button onClick={() => setShowModal(false)} className="text-[#555] hover:text-white transition-colors p-2">
                <X size={24} />
              </button>
            </div>

            {/* Modal Tabs */}
            <div className="flex border-b border-white/5 bg-black/20">
                {[
                    { id: 'dados', label: 'Dados Gerais', icon: <Info size={14}/> },
                    { id: 'questor', label: 'Integração Questor', icon: <Database size={14}/> },
                    { id: 'estrutura', label: 'Estrutura (Blocos)', icon: <Layers size={14}/>, disabled: !editingEmp }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => !tab.disabled && setActiveTab(tab.id)}
                        disabled={tab.disabled}
                        className={`px-8 py-4 text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-2 transition-all border-b-2 ${
                            activeTab === tab.id 
                            ? 'text-[#ff4d00] border-[#ff4d00] bg-[#ff4d00]/5' 
                            : 'text-[#444] border-transparent hover:text-[#888] disabled:opacity-30'
                        }`}
                    >
                        {tab.icon} {tab.label}
                    </button>
                ))}
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
              
              {activeTab === 'dados' && (
                <div className="grid grid-cols-2 gap-6 animate-in slide-in-from-left-2 duration-500">
                    <div className="space-y-4">
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Nome do Empreendimento</label>
                            <input value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">CNPJ</label>
                                <input value={formData.cnpj} onChange={(e) => setFormData({...formData, cnpj: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">CNO</label>
                                <input value={formData.cno} onChange={(e) => setFormData({...formData, cno: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50" />
                            </div>
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Endereço Completo</label>
                            <input value={formData.endereco} onChange={(e) => setFormData({...formData, endereco: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50" />
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Metragem Total (m²)</label>
                                <input type="number" value={formData.metragem} onChange={(e) => setFormData({...formData, metragem: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Custo Orçado</label>
                                <input type="number" value={formData.custo} onChange={(e) => setFormData({...formData, custo: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Adere ao RET?</label>
                                <select value={formData.ret} onChange={(e) => setFormData({...formData, ret: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50">
                                    <option value="N">Não</option>
                                    <option value="S">Sim</option>
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Controle Status</label>
                                <select value={formData.ativo} onChange={(e) => setFormData({...formData, ativo: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50">
                                    <option value="S">Ativo (Em Obras)</option>
                                    <option value="N">Concluído</option>
                                    <option value="I">Inativo</option>
                                </select>
                            </div>
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Data de Conclusão</label>
                            <input type="date" value={formData.data_conclusao} onChange={(e) => setFormData({...formData, data_conclusao: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50" />
                        </div>
                    </div>
                </div>
              )}

              {activeTab === 'questor' && (
                <div className="space-y-8 animate-in slide-in-from-right-2 duration-500">
                    <div className="bg-[#ff4d00]/5 border border-[#ff4d00]/20 p-4 rounded-sm flex items-start gap-4">
                        <AlertCircle className="text-[#ff4d00] shrink-0" size={18} />
                        <div>
                            <h4 className="text-[10px] font-black text-white uppercase tracking-widest">Mapeamento Contábil Especial</h4>
                            <p className="text-[10px] text-[#888] leading-relaxed mt-1">Os campos abaixo definem o de-para automático entre os movimentos do Vulcano e o Plano de Contas Especial da empresa selecionada no Questor. Use o searchable select para localizar a conta analítica.</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-6">
                        {renderAccountInput("Conta Disponível (Caixa/Banco)", "conta_caixa", "1.1.01")}
                        {renderAccountInput("Conta Clientes (AVR)", "conta_clientes", "1.1.03")}
                        {renderAccountInput("Conta Adiantamento Clientes", "conta_adi_cli", "1.1.03")}
                        
                        {renderAccountInput("Estoque Andamento", "conta_estand", "1.1.04")}
                        {renderAccountInput("Estoque Concluído", "conta_estcon", "1.1.04")}
                        
                        {renderAccountInput("Conta Receita Venda (DRE)", "conta_rec", "4")}
                        {renderAccountInput("Variação Monetária (DRE)", "conta_variacao", "4")}
                        {renderAccountInput("Conta Devolução (DRE)", "conta_devolucao", "4")}
                        {renderAccountInput("Conta Despesa Tributária", "conta_despesa", "3")}
                    </div>

                    <div className="grid grid-cols-2 gap-6 pt-6 border-t border-white/5">
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Centro de Custo Questor</label>
                            <select value={formData.centro_custo} onChange={(e) => setFormData({...formData, centro_custo: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50">
                                <option value="0">Sem mapeamento</option>
                                {centrosCusto.map(cc => <option key={cc.id} value={cc.id}>{cc.id} - {cc.descricao}</option>)}
                            </select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Hist. Venda</label>
                                <select value={formData.hist_venda} onChange={(e) => setFormData({...formData, hist_venda: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[#555] uppercase tracking-widest">Hist. Receb.</label>
                                <select value={formData.hist_recebimento} onChange={(e) => setFormData({...formData, hist_recebimento: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-white outline-none focus:border-[#ff4d00]/50">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
              )}

              {activeTab === 'estrutura' && (
                <div className="space-y-8 animate-in zoom-in-95 duration-500">
                    <div className="grid grid-cols-12 gap-8">
                        {/* Blocos List */}
                        <div className="col-span-4 border-r border-white/5 pr-8 space-y-4">
                            <h4 className="text-[10px] font-black text-[#ff4d00] uppercase tracking-widest flex items-center gap-2">
                                <Layers size={14}/> Blocos Estruturais
                            </h4>
                            
                            <div className="flex gap-2">
                                <input 
                                    value={newBlocoName} 
                                    onChange={(e) => setNewBlocoName(e.target.value)}
                                    placeholder="Ex: Bloco A"
                                    className="flex-1 bg-black/40 border border-white/5 p-2 text-xs text-white outline-none focus:border-[#ff4d00]/50"
                                />
                                <button onClick={handleAddBloco} className="bg-white/5 p-2 text-[#ff4d00] border border-white/10 hover:bg-[#ff4d00] hover:text-black transition-all">
                                    <Plus size={16}/>
                                </button>
                            </div>

                            <div className="space-y-2">
                                {loadingEstrutura ? (
                                    <div className="py-10 text-center"><Loader2 className="animate-spin mx-auto text-[#555]"/></div>
                                ) : blocos.map(b => (
                                    <div key={b.id} className="group p-3 bg-white/5 border border-white/5 flex justify-between items-center hover:border-[#ff4d00]/30 transition-all">
                                        <div className="flex items-center gap-3">
                                            <span className="text-[10px] font-black text-[#555]">{b.id}</span>
                                            <span className="text-[11px] font-bold text-white uppercase">{b.nome}</span>
                                        </div>
                                        <button onClick={() => handleDeleteEstrutura('bloco', b.id)} className="opacity-0 group-hover:opacity-100 p-1 hover:text-[#ff3b30] transition-all"><Trash2 size={12}/></button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Unidades List */}
                        <div className="col-span-8 space-y-4">
                            <h4 className="text-[10px] font-black text-[#ff4d00] uppercase tracking-widest flex items-center gap-2">
                                <Home size={14}/> Unidades Imobiliárias
                            </h4>
                            
                            <div className="grid grid-cols-5 gap-2">
                                <select 
                                    value={newUnidade.id_bloco} 
                                    onChange={(e) => setNewUnidade({...newUnidade, id_bloco: e.target.value})}
                                    className="bg-black/40 border border-white/5 p-2 text-[10px] text-white outline-none"
                                >
                                    <option value="">Bloco...</option>
                                    {blocos.map(b => <option key={b.id} value={b.id}>{b.nome}</option>)}
                                </select>
                                <input 
                                    placeholder="Nº Unidade" 
                                    value={newUnidade.descricao}
                                    onChange={(e) => setNewUnidade({...newUnidade, descricao: e.target.value})}
                                    className="bg-black/40 border border-white/5 p-2 text-[10px] text-white outline-none"
                                />
                                <input 
                                    placeholder="Metragem" 
                                    type="number"
                                    value={newUnidade.metragem}
                                    onChange={(e) => setNewUnidade({...newUnidade, metragem: e.target.value})}
                                    className="bg-black/40 border border-white/5 p-2 text-[10px] text-white outline-none"
                                />
                                <input 
                                    placeholder="Insc. Imob" 
                                    value={newUnidade.inscricao}
                                    onChange={(e) => setNewUnidade({...newUnidade, inscricao: e.target.value})}
                                    className="bg-black/40 border border-white/5 p-2 text-[10px] text-white outline-none"
                                />
                                <button onClick={handleAddUnidade} className="bg-[#ff4d00]/10 text-[#ff4d00] border border-[#ff4d00]/30 py-2 text-[10px] font-black uppercase hover:bg-[#ff4d00] hover:text-black transition-all">Add</button>
                            </div>

                            <div className="bg-black/20 border border-white/5 rounded-sm overflow-hidden">
                                <table className="w-full text-left text-[10px]">
                                    <thead className="bg-white/5 text-[#555] font-black uppercase tracking-widest">
                                        <tr>
                                            <th className="p-3">Bloco</th>
                                            <th className="p-3">Descrição/Nº</th>
                                            <th className="p-3">Metragem</th>
                                            <th className="p-3">Inc. Questor</th>
                                            <th className="p-3 text-right">Ação</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {unidades.map(u => (
                                            <tr key={u.id} className="hover:bg-white/5 transition-colors">
                                                <td className="p-3 font-bold text-[#888]">{blocos.find(b => b.id === u.id_bloco)?.nome || u.id_bloco}</td>
                                                <td className="p-3 font-black text-white">{u.descricao}</td>
                                                <td className="p-3 text-[#34c759] font-mono">{u.metragem} m²</td>
                                                <td className="p-3 text-[#555] font-mono">{u.inscricao || '---'}</td>
                                                <td className="p-3 text-right">
                                                    <button onClick={() => handleDeleteEstrutura('unidade', u.id)} className="text-[#555] hover:text-[#ff3b30] transition-colors"><Trash2 size={12}/></button>
                                                </td>
                                            </tr>
                                        ))}
                                        {!unidades.length && !loadingEstrutura && (
                                            <tr>
                                                <td colSpan="5" className="p-10 text-center text-[#444] font-black uppercase tracking-[0.3em]">Nenhuma unidade vinculada</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
              )}

            </div>

            {/* Footer Modal */}
            <div className="p-6 border-t border-white/5 bg-black/40 flex justify-end gap-4">
              <button onClick={() => setShowModal(false)} className="px-6 py-2.5 text-[10px] font-black uppercase tracking-widest text-[#555] hover:text-white transition-colors">Cancelar</button>
              <button 
                onClick={handleSave}
                className="px-8 py-2.5 bg-[#ff4d00] text-black font-black text-[10px] uppercase tracking-widest hover:bg-white transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(255,77,0,0.2)]"
              >
                <Save size={16} /> Salvar Alterações
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
