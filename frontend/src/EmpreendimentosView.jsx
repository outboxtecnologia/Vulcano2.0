import React, { useState, useEffect } from 'react';
import { 
  Building2, Plus, Edit, Trash2, Search, X, Check, Loader2, 
  Settings, Database, Construction, Layers, Home, Ruler,
  ChevronRight, ArrowRight, Save, Info, AlertCircle
} from 'lucide-react';
import { API_BASE } from './apiBase';

// A API devolve {"detail": "..."} nos erros 500 (ex.: Firebird fora do ar).
// Sem esta guarda o objeto de erro cai direto no estado e quebra o .map() na renderizacao.
const asArray = (v) => (Array.isArray(v) ? v : []);

// Picker de conta contábil do plano Questor da empresa: busca por código,
// classificação ou nome (sem acento), sintéticas visíveis mas não
// selecionáveis, e digitação manual do código (Enter/blur com dígitos).
const ContaPicker = ({ label, value, onChange, contas, prefix, loading }) => {
  const [aberto, setAberto] = useState(false);
  const [busca, setBusca] = useState('');
  const norm = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const sel = contas.find(c => String(c.id) === String(value || ''));
  const base = contas.filter(c => !prefix || String(c.classificacao || '').startsWith(prefix));
  const t = norm(busca.trim());
  const filtradas = !t ? base : base.filter(c =>
    String(c.id).includes(t) || String(c.classificacao || '').includes(t) || norm(c.descricao).includes(t));
  const commitDigitos = () => {
    const d = busca.trim();
    if (/^\d+$/.test(d)) onChange(d);
  };
  return (
    <div className="space-y-1">
      <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">{label}</label>
      <div className="relative">
        <input
          value={aberto ? busca : (sel ? `${sel.id} — ${sel.descricao}` : String(value || '') === '0' ? '' : String(value || ''))}
          onFocus={() => { setAberto(true); setBusca(''); }}
          onChange={(e) => setBusca(e.target.value)}
          onBlur={() => setTimeout(() => { commitDigitos(); setAberto(false); }, 150)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              const d = busca.trim();
              if (/^\d+$/.test(d)) commitDigitos();
              else if (filtradas.length && filtradas[0].tipo !== 1) onChange(String(filtradas[0].id));
              setAberto(false); e.target.blur();
            }
            if (e.key === 'Escape') { setAberto(false); e.target.blur(); }
          }}
          placeholder={loading ? 'Carregando plano de contas...' : 'Código, classificação ou nome...'}
          className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50 transition-all font-mono"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-30 pointer-events-none">
          <Search size={12} className="text-[var(--v-accent)]" />
        </div>
        {aberto && filtradas.length > 0 && (
          <div className="absolute z-50 left-0 right-0 mt-1 max-h-52 overflow-y-auto rounded border border-white/10 shadow-2xl custom-scrollbar" style={{ background: '#141110' }}>
            {filtradas.slice(0, 40).map(c => (
              <button type="button" key={c.id} disabled={c.tipo === 1}
                onMouseDown={(e) => { e.preventDefault(); if (c.tipo !== 1) { onChange(String(c.id)); setAberto(false); } }}
                className={`w-full text-left px-2.5 py-1.5 text-[10.5px] ${c.tipo === 1 ? 'opacity-40 cursor-default' : 'hover:bg-white/10 cursor-pointer'}`}>
                <span className="font-mono text-[var(--v-accent)]">{c.classificacao}</span>
                <span className="font-mono text-[var(--v-text-faint)]"> #{c.id}</span>
                <span className="text-[var(--v-text-bold)]"> — {c.descricao}</span>
                {c.tipo === 1 && <span className="text-[9px] uppercase"> (sintética)</span>}
              </button>
            ))}
            {filtradas.length > 40 && (
              <div className="px-2.5 py-1 text-[9px] text-[var(--v-text-faint)]">… e mais {filtradas.length - 40} conta(s) — refine a busca</div>
            )}
          </div>
        )}
      </div>
      <p className="text-[9px] text-[var(--v-text-faint)] font-medium truncate" title={sel ? sel.descricao : ''}>
        Questor ID: {value || '0'} {sel ? `— ${sel.descricao}` : ''}
      </p>
    </div>
  );
};

export const EmpreendimentosView = ({ selectedEmpresa, onNavigate }) => {
  const [empreendimentos, setEmpreendimentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingEmp, setEditingEmp] = useState(null);
  const [activeTab, setActiveTab] = useState('dados'); // 'dados', 'questor', 'estrutura'
  const [searchQuery, setSearchQuery] = useState('');

  // Pickers "Puxar do Questor" (CNPJ do estab / CNO da obra)
  const [questorEstabs, setQuestorEstabs] = useState(null);   // null = ainda nao buscado
  const [questorObras, setQuestorObras] = useState(null);
  const [pickerOpen, setPickerOpen] = useState(null);         // null | 'cnpj' | 'cno'
  const [loadingPicker, setLoadingPicker] = useState(false);

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
    datainicioret: '',
    aliqret: 0,
    ativo: 'S',
    obra_concluida: 'N',
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
    hist_baixaadi: 0,
    hist_estorno_saldo: 0,
    hist_adiantamento: 0,
    hist_aprcusto: 0,
    hist_despesa: 0,
    hist_estorno_custo: 0
  });

  // Endereco estruturado (layout DIMOB) — persiste no banco proprio do app
  const EMPTY_ENDERECO = { tipo_logradouro: '', logradouro: '', numero: '', complemento: '', bairro: '', cep: '', uf: '', codigo_munic: '', fonte: 'MANUAL', codigo_outemp: null, codigo_estab: null };
  const [enderecoForm, setEnderecoForm] = useState(EMPTY_ENDERECO);

  useEffect(() => {
    fetchEmpreendimentos();
    // caches dos pickers sao por empresa — trocar de empresa invalida
    setQuestorEstabs(null);
    setQuestorObras(null);
    setPickerOpen(null);
    if (selectedEmpresa) {
        fetchQuestorData();
    }
  }, [selectedEmpresa]);

  // guarda contra resposta stale do fetch de endereco (modal reaberto p/ outro emp)
  const enderecoReqRef = React.useRef(0);

  const fetchEmpreendimentos = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      setEmpreendimentos(asArray(data));
      setError(null);
      setLoading(false);
    } catch (err) {
      setEmpreendimentos([]);
      setError("Falha ao comunicar com node Vulcano");
      setLoading(false);
    }
  };

  const fetchQuestorData = async () => {
    setLoadingQuestor(true);
    try {
        const [pc, cc, hi] = await Promise.all([
            fetch(`${API_BASE}/api/questor/plano-contas-espec?empresa_id=${selectedEmpresa}`).then(r => r.json()),
            fetch(`${API_BASE}/api/questor/centrocusto?empresa_id=${selectedEmpresa}`).then(r => r.json()),
            fetch(`${API_BASE}/api/questor/historicos`).then(r => r.json())
        ]);
        setPlanoContas(asArray(pc?.contas));
        setCentrosCusto(asArray(cc));
        setHistoricos(asArray(hi));
    } catch (e) {
        console.error("Erro Questor Mapping:", e);
        setPlanoContas([]);
        setCentrosCusto([]);
        setHistoricos([]);
    } finally {
        setLoadingQuestor(false);
    }
  };

  const fetchEstrutura = async (empId) => {
    setLoadingEstrutura(true);
    try {
        const res = await fetch(`${API_BASE}/api/vulcano/empreendimentos/${empId}/detalhes?incluir_vendidas=true`);
        const data = await res.json();
        setBlocos(asArray(data?.blocos));
        setUnidades(asArray(data?.unidades));
    } catch (e) {
        setBlocos([]);
        setUnidades([]);
        console.error("Erro Estrutura:", e);
    } finally {
        setLoadingEstrutura(false);
    }
  };

  const fetchEndereco = async (empId, emp) => {
    const reqId = ++enderecoReqRef.current;
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/empreendimentos/${empId}/endereco`);
      const data = await res.json();
      if (reqId !== enderecoReqRef.current) return; // resposta stale: outro modal foi aberto
      if (res.ok && data?.endereco) {
        setEnderecoForm({ ...data.endereco, fonte: data.fonte === 'legado' ? 'MANUAL' : (data.fonte || 'MANUAL'), codigo_outemp: data.codigo_outemp, codigo_estab: data.codigo_estab });
        return;
      }
    } catch (e) { console.error('Erro endereco:', e); }
    if (reqId !== enderecoReqRef.current) return;
    // fallback: campos legados achatados do proprio emp
    setEnderecoForm({ ...EMPTY_ENDERECO, logradouro: emp?.endereco || '', cep: emp?.cep || '', uf: emp?.siglaestado || '', codigo_munic: emp?.codigomunic || '' });
  };

  const handleOpenModal = (emp = null) => {
    setPickerOpen(null);
    if (emp) {
      setEditingEmp(emp);
      setFormData({
        ...emp,
        ret: emp.ret || 'N',
        datainicioret: emp.datainicioret || '',
        aliqret: emp.aliqret || 0,
        ativo: emp.ativo || 'S',
        obra_concluida: emp.obra_concluida || 'N'
      });
      fetchEstrutura(emp.id);
      fetchEndereco(emp.id, emp);
    } else {
      setEditingEmp(null);
      setFormData({
        nome: '', cnpj: '', cno: '', metragem: 0, custo: 0, endereco: '',
        ret: 'N', datainicioret: '', aliqret: 0,
        ativo: 'S', obra_concluida: 'N', data_conclusao: '',
        conta_caixa: 0, conta_clientes: 0, conta_adi_cli: 0,
        conta_estand: 0, conta_estcon: 0, conta_despesa: 0, conta_rec: 0,
        conta_variacao: 0, conta_devolucao: 0, centro_custo: 0,
        hist_venda: 0, hist_recebimento: 0, hist_variacao: 0, hist_distrato: 0,
        hist_baixaadi: 0, hist_estorno_saldo: 0, hist_adiantamento: 0, hist_aprcusto: 0,
        hist_despesa: 0, hist_estorno_custo: 0
      });
      setEnderecoForm(EMPTY_ENDERECO);
      setBlocos([]);
      setUnidades([]);
    }
    setActiveTab('dados');
    setShowModal(true);
  };

  // Pickers "Puxar do Questor"
  const handleOpenPicker = async (kind) => {
    if (pickerOpen === kind) { setPickerOpen(null); return; }
    setPickerOpen(kind);
    const cached = kind === 'cnpj' ? questorEstabs : questorObras;
    if (cached !== null) return;
    setLoadingPicker(true);
    try {
      if (kind === 'cnpj') {
        const r = await fetch(`${API_BASE}/api/questor/estabs?empresa_id=${selectedEmpresa}`).then(r => r.json());
        setQuestorEstabs(asArray(r?.estabs));
      } else {
        const r = await fetch(`${API_BASE}/api/questor/obras-cno?empresa_id=${selectedEmpresa}`).then(r => r.json());
        setQuestorObras(asArray(r?.obras));
      }
    } catch (e) {
      console.error('Erro picker Questor:', e);
      // null (nao []) para permitir retry na proxima abertura apos falha transitoria
      if (kind === 'cnpj') setQuestorEstabs(null); else setQuestorObras(null);
      setPickerOpen(null);
      alert('Falha ao consultar o Questor — tente abrir o picker novamente.');
    } finally {
      setLoadingPicker(false);
    }
  };

  const aplicarEnderecoQuestor = (endereco, fonte, extra) => {
    // Preenche o endereco estruturado a partir do Questor apenas se vier algo util
    if (!endereco || !(endereco.logradouro || endereco.cep)) return;
    setEnderecoForm(prev => ({
      ...prev,
      ...endereco,
      fonte,
      codigo_outemp: extra?.codigo_outemp ?? prev.codigo_outemp,
      codigo_estab: extra?.codigo_estab ?? prev.codigo_estab,
    }));
  };

  const handlePickEstab = (estab) => {
    setFormData(f => ({ ...f, cnpj: estab.cnpj, codigoestab: String(estab.codigoestab) }));
    aplicarEnderecoQuestor(estab.endereco, 'QUESTOR_ESTAB', { codigo_estab: estab.codigoestab });
    setPickerOpen(null);
  };

  const handlePickObra = (obra) => {
    setFormData(f => ({ ...f, cno: obra.cno }));
    aplicarEnderecoQuestor(obra.endereco, 'QUESTOR_OBRA', { codigo_outemp: obra.codigooutemp });
    setPickerOpen(null);
  };

  // ── Importação da estrutura via matrícula de incorporação (PDF → Vertex) ──
  const [matriculaPreview, setMatriculaPreview] = useState(null);
  const [matriculaLoading, setMatriculaLoading] = useState(false);
  const [metragemCampo, setMetragemCampo] = useState('area_privativa_m2');
  const [incluirVaga, setIncluirVaga] = useState(false);
  const [importandoEstrutura, setImportandoEstrutura] = useState(false);
  const matriculaInputRef = React.useRef(null);
  const [chatMsg, setChatMsg] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [chatBusy, setChatBusy] = useState(false);

  const enviarChatMatricula = async () => {
    const msg = chatMsg.trim();
    if (!msg || !matriculaPreview?.sessao_id) return;
    setChatBusy(true);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/matricula/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessao_id: matriculaPreview.sessao_id, mensagem: msg })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      setChatLog(l => [...l, { pergunta: msg, resposta: data.resposta,
                               adicionadas: data.adicionadas || [], corrigidas: data.corrigidas || [] }]);
      setMatriculaPreview(data.resultado);   // prévia + críticas atualizadas
      setChatMsg('');
    } catch (e) { alert('Falha na verificação: ' + e.message); }
    finally { setChatBusy(false); }
  };

  const handleUploadMatricula = async (file) => {
    if (!file) return;
    setMatriculaLoading(true);
    setMatriculaPreview(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API_BASE}/api/vulcano/matricula/extrair`, { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      setMatriculaPreview(data);
    } catch (e) {
      alert('Falha na leitura da matrícula: ' + e.message);
    } finally {
      setMatriculaLoading(false);
      if (matriculaInputRef.current) matriculaInputRef.current.value = '';
    }
  };

  const descricaoUnidadeMatricula = (u) => {
    const tipo = (u.tipo || '').toUpperCase().startsWith('APART') ? 'APTO' : (u.tipo || 'UNID').toUpperCase().slice(0, 12);
    let d = `${tipo} ${u.numero}`;
    if (incluirVaga && u.vaga) d += ` - VAGA ${u.vaga.toUpperCase()}`;
    return d;
  };

  const handleGravarEstrutura = async () => {
    if (!matriculaPreview || !editingEmp) return;
    const porBloco = {};
    matriculaPreview.unidades.forEach(u => {
      (porBloco[u.bloco] = porBloco[u.bloco] || []).push({
        descricao: descricaoUnidadeMatricula(u),
        metragem: u[metragemCampo] ?? null,
      });
    });
    const payload = {
      empreendimento_id: editingEmp.id,
      sessao_id: matriculaPreview.sessao_id || null,
      blocos: Object.entries(porBloco).map(([nome, unidades]) => ({ nome, unidades })),
    };
    setImportandoEstrutura(true);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/estrutura/importar`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      alert(`Importado: ${data.blocos_criados} bloco(s) criado(s), ${data.blocos_reaproveitados} reaproveitado(s), ${data.unidades_criadas} unidade(s) criada(s), ${data.unidades_puladas} já existiam.`);
      setMatriculaPreview(null);
      fetchEstrutura(editingEmp.id);
    } catch (e) {
      alert('Falha ao gravar estrutura: ' + e.message);
    } finally {
      setImportandoEstrutura(false);
    }
  };

  const aplicarCadastroMatricula = () => {
    const e = matriculaPreview?.empreendimento;
    if (!e) return;
    if (e.endereco?.logradouro || e.endereco?.cep) {
      setEnderecoForm(prev => ({
        ...prev,
        logradouro: e.endereco.logradouro || prev.logradouro,
        numero: e.endereco.numero || prev.numero,
        complemento: e.endereco.complemento || prev.complemento,
        bairro: e.endereco.bairro || prev.bairro,
        cep: e.endereco.cep || prev.cep,
        uf: e.endereco.uf || prev.uf,
        fonte: 'MANUAL',
      }));
    }
    if (e.nome && !formData.nome) setFormData(f => ({ ...f, nome: e.nome }));
    setActiveTab('dados');
    alert('Endereço da matrícula aplicado à aba Dados Gerais — confira e salve.');
  };

  const handleSave = async () => {
    const method = editingEmp ? 'PATCH' : 'POST';
    const url = editingEmp 
      ? `${API_BASE}/api/vulcano/empreendimentos/${editingEmp.id}`
      : `${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`;
    
    // Endereco legado = concatenacao do estruturado (compatibilidade).
    // Sem fallback pro formData.endereco antigo: o enderecoForm e a fonte de
    // verdade (carregado do banco do app ou do proprio legado ao abrir o modal),
    // entao limpar os campos limpa o endereco de fato.
    const endLegado = [
        [enderecoForm.logradouro, enderecoForm.numero].filter(Boolean).join(', '),
        enderecoForm.complemento,
        enderecoForm.bairro ? `- ${enderecoForm.bairro}` : ''
    ].filter(Boolean).join(' ').trim();

    // Ensure numeric fields are correctly typed
    const payload = {
        ...formData,
        endereco: endLegado,
        cep: enderecoForm.cep || '',
        siglaestado: enderecoForm.uf || '',
        codigomunic: String(enderecoForm.codigo_munic || ''),
        obra_concluida: formData.obra_concluida || 'N',
        empresa_id: parseInt(selectedEmpresa),
        metragem: parseFloat(formData.metragem || 0),
        custo: parseFloat(formData.custo || 0),
        aliqret: parseFloat(formData.aliqret || 0),
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
        hist_baixaadi: parseInt(formData.hist_baixaadi || 0),
        hist_estorno_saldo: parseInt(formData.hist_estorno_saldo || 0),
        hist_adiantamento: parseInt(formData.hist_adiantamento || 0),
        hist_aprcusto: parseInt(formData.hist_aprcusto || 0),
        hist_despesa: parseInt(formData.hist_despesa || 0),
        hist_estorno_custo: parseInt(formData.hist_estorno_custo || 0)
    };

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        // Persiste o endereco estruturado (banco do app) apos salvar o cadastro
        const body = await res.json().catch(() => ({}));
        const empId = editingEmp ? editingEmp.id : body?.id;
        // Em edicao o PUT roda sempre (permite LIMPAR o endereco); em criacao, so
        // se algo foi preenchido.
        if (empId && (editingEmp || enderecoForm.logradouro || enderecoForm.cep || enderecoForm.bairro)) {
          try {
            const resEnd = await fetch(`${API_BASE}/api/vulcano/empreendimentos/${empId}/endereco`, {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ...enderecoForm, codigo_munic: String(enderecoForm.codigo_munic || '') })
            });
            if (!resEnd.ok) {
              const errEnd = await resEnd.json().catch(() => ({}));
              alert("Cadastro salvo, mas o endereço estruturado falhou: " + (errEnd?.detail || resEnd.status));
            }
          } catch (e) {
            alert("Cadastro salvo, mas o endereço estruturado falhou (rede).");
          }
        }
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

  // Picker do plano de contas Questor (Melhorias 2, item 1): datalist não
  // escala p/ milhares de contas — dropdown próprio com busca por código,
  // classificação ou nome; sintéticas (tipo=1) aparecem mas não selecionam;
  // digitação manual do código continua valendo (blur/Enter com dígitos).
  const renderAccountInput = (label, name, prefix) => {
    return <ContaPicker key={name} label={label} prefix={prefix}
        value={formData[name]} contas={planoContas} loading={loadingQuestor}
        onChange={(v) => setFormData(f => ({ ...f, [name]: v }))} />;
  };

  if (loading && !empreendimentos.length) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-20 gap-4">
        <Loader2 className="animate-spin text-[var(--v-accent)]" size={40} />
        <span className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">Mapeando Infraestruturas...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex justify-between items-end border-b border-white/5 pb-6">
        <div>
          <h2 className="font-headline text-3xl font-black tracking-tight text-[var(--v-text-bold)] uppercase italic">Central de Empreendimentos</h2>
          <p className="text-[10px] text-[var(--v-accent)] font-black uppercase tracking-[0.4em] mt-1">Gestão de Nodes & Infraestrutura Vulcano</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--v-text-faint)]" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar por nome, nº cadastro, CNPJ ou CNO..."
              className="w-80 bg-black/40 border border-white/5 rounded-[var(--v-radius)] pl-9 pr-3 py-3 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50 transition-all placeholder:text-[var(--v-text-faint)]"
            />
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="bg-[var(--v-accent)] text-black px-6 py-3 rounded-[var(--v-radius)] font-black text-[10px] uppercase tracking-[0.2em] flex items-center gap-2 hover:bg-white transition-all shadow-[0_0_20px_rgba(255,77,0,0.3)] group"
          >
            <Plus size={16} className="group-hover:rotate-90 transition-transform" /> Novo Empreendimento
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {empreendimentos.filter(emp => {
          const q = searchQuery.trim().toLowerCase();
          if (!q) return true;
          return [emp.nome, String(emp.id), emp.cnpj, emp.cno].some(v => (v || '').toLowerCase().includes(q));
        }).map(emp => (
          <div key={emp.id} className="group relative">
            <div className="p-6 bg-black/40 backdrop-blur-md border border-white/5 rounded-[var(--v-radius)] hover:border-[#ff4d00]/30 transition-all duration-300 flex flex-col h-full gap-4">
              <div className="flex justify-between items-start">
                <div className="w-10 h-10 bg-white/5 flex items-center justify-center rounded-[var(--v-radius)]">
                  <Building2 size={20} className={emp.ativo === 'N' ? "text-[var(--v-accent-3)]" : "text-[var(--v-accent)]"} />
                </div>
                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => handleOpenModal(emp)} className="p-2 bg-white/5 hover:bg-[var(--v-accent)]/10 hover:text-[var(--v-accent)] rounded-[var(--v-radius)] transition-colors"><Edit size={14}/></button>
                  <button onClick={() => handleDelete(emp.id)} className="p-2 bg-white/5 hover:bg-[#ff3b30]/10 hover:text-[#ff3b30] rounded-[var(--v-radius)] transition-colors"><Trash2 size={14}/></button>
                </div>
              </div>
              
              <div className="space-y-1">
                <h3 className="font-headline font-black text-[var(--v-text-bold)] uppercase tracking-wider text-sm">{emp.nome}</h3>
                <p className="text-[10px] text-[var(--v-text-faint)] font-bold uppercase py-1 border-b border-white/5">CNO: {emp.cno || 'Não Informado'}</p>
                <p className="text-[10px] text-[var(--v-text-faint)] font-bold uppercase py-1 border-b border-white/5">CNPJ: {emp.cnpj || '—'}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-2">
                <div className="space-y-1">
                  <span className="text-[9px] text-[var(--v-text-faint)] font-black uppercase tracking-widest block">Metragem</span>
                  <div className="flex items-center gap-1.5 text-[var(--v-text-bold)]/80 font-mono text-[11px]">
                    <Ruler size={12} className="text-[var(--v-accent)]" /> {emp.metragem || 0} m²
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-[9px] text-[var(--v-text-faint)] font-black uppercase tracking-widest block">Custo Orc.</span>
                  <div className="flex items-center gap-1.5 text-[var(--v-text-bold)]/80 font-mono text-[11px]">
                    <Database size={12} className="text-[var(--v-accent-3)]" /> {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(emp.custo || 0)}
                  </div>
                </div>
              </div>

              <div className="mt-auto pt-4 flex items-center justify-between">
                 <div className="flex gap-2">
                    {emp.ret === 'S' && <span className="text-[8px] bg-[var(--v-accent)]/10 text-[var(--v-accent)] border border-[#ff4d00]/20 px-1.5 py-0.5 rounded-[var(--v-radius)] font-black uppercase">RET</span>}
                    {emp.ativo === 'N' && <span className="text-[8px] bg-[#ff3b30]/10 text-[#ff3b30] border border-[#ff3b30]/20 px-1.5 py-0.5 rounded-[var(--v-radius)] font-black uppercase">Inativo</span>}
                    {emp.obra_concluida === 'S' ? 
                       <span className="text-[8px] bg-[#34c759]/10 text-[var(--v-accent-3)] border border-[#34c759]/20 px-1.5 py-0.5 rounded-[var(--v-radius)] font-black uppercase">Concluído</span> :
                       <span className="text-[8px] bg-[#007aff]/10 text-[var(--v-accent-4)] border border-[#007aff]/20 px-1.5 py-0.5 rounded-[var(--v-radius)] font-black uppercase">Em Obras</span>
                    }
                 </div>
                 <div className="flex items-center gap-2">
                   <div className="text-[9px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">ID {emp.id}</div>
                   {onNavigate && (
                     <button
                       onClick={(e) => { e.stopPropagation(); onNavigate('custos'); }}
                       title="Abrir Fechamento de Custos deste empreendimento"
                       className="flex items-center gap-1 px-2 py-1 bg-[var(--v-accent)]/10 hover:bg-[var(--v-accent)]/25 border border-[#ff4d00]/20 rounded-[var(--v-radius)] text-[8px] font-black uppercase tracking-widest text-[var(--v-accent)] transition-all group-hover:opacity-100 opacity-60"
                     >
                       Custos <ArrowRight size={10} /> 
                     </button>
                   )}
                 </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/90 backdrop-blur-sm" onClick={() => setShowModal(false)}></div>
          <div className="relative w-[95vw] max-w-[1600px] h-[95vh] bg-[var(--v-deep)] border border-white/10 shadow-2xl flex flex-col overflow-hidden">
            
            {/* Header Modal */}
            <div className="p-6 border-b border-white/5 flex justify-between items-center bg-black/40">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-[var(--v-accent)] text-black flex items-center justify-center rounded-[var(--v-radius)]">
                  <Building2 size={24} />
                </div>
                <div>
                  <h3 className="font-headline text-xl font-black text-[var(--v-text-bold)] uppercase tracking-tight">
                    {editingEmp ? 'Editar Empreendimento' : 'Novo Empreendimento'}
                  </h3>
                  <p className="text-[10px] text-[var(--v-text-faint)] font-black uppercase tracking-widest">Configuração de Parâmetros e Mapeamento</p>
                </div>
              </div>
              <button onClick={() => setShowModal(false)} className="text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] transition-colors p-2">
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
                            ? 'text-[var(--v-accent)] border-[#ff4d00] bg-[var(--v-accent)]/5' 
                            : 'text-[var(--v-text-faint)] border-transparent hover:text-[var(--v-text-muted)] disabled:opacity-30'
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
                            <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Nome do Empreendimento</label>
                            <input value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1 relative">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">CNPJ RET</label>
                                <div className="flex gap-1">
                                    <input value={formData.cnpj} onChange={(e) => setFormData({...formData, cnpj: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                    <button type="button" onClick={() => handleOpenPicker('cnpj')} title="Puxar do Questor (estabelecimentos da empresa)"
                                        className="px-2.5 bg-white/5 hover:bg-[var(--v-accent)]/15 border border-white/5 rounded-[var(--v-radius)] text-[var(--v-accent)] transition-colors shrink-0">
                                        <Database size={14}/>
                                    </button>
                                </div>
                                {pickerOpen === 'cnpj' && (
                                    <div className="absolute z-30 top-full left-0 right-0 mt-1 max-h-56 overflow-y-auto bg-black/95 border border-white/10 rounded-[var(--v-radius)] shadow-2xl custom-scrollbar">
                                        {loadingPicker ? <div className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase animate-pulse">Buscando no Questor...</div> :
                                         !(questorEstabs || []).length ? <div className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase">Nenhum estabelecimento</div> :
                                         (questorEstabs || []).map(es => (
                                            <button key={es.codigoestab} type="button" onClick={() => handlePickEstab(es)}
                                                className="w-full text-left px-3 py-2 text-[11px] text-[var(--v-text-bold)] hover:bg-[var(--v-accent)]/10 border-b border-white/5 font-mono">
                                                Estab {es.codigoestab} — {es.cnpj || 'sem CNPJ'}
                                                <span className="block text-[9px] text-[var(--v-text-faint)] font-sans">{es.endereco?.logradouro}{es.endereco?.numero ? `, ${es.endereco.numero}` : ''} {es.endereco?.bairro}</span>
                                            </button>
                                         ))}
                                    </div>
                                )}
                            </div>
                            <div className="space-y-1 relative">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">CNO</label>
                                <div className="flex gap-1">
                                    <input value={formData.cno} onChange={(e) => setFormData({...formData, cno: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                    <button type="button" onClick={() => handleOpenPicker('cno')} title="Puxar do Questor (obras/CNO da empresa)"
                                        className="px-2.5 bg-white/5 hover:bg-[var(--v-accent)]/15 border border-white/5 rounded-[var(--v-radius)] text-[var(--v-accent)] transition-colors shrink-0">
                                        <Database size={14}/>
                                    </button>
                                </div>
                                {pickerOpen === 'cno' && (
                                    <div className="absolute z-30 top-full left-0 right-0 mt-1 max-h-56 overflow-y-auto bg-black/95 border border-white/10 rounded-[var(--v-radius)] shadow-2xl custom-scrollbar">
                                        {loadingPicker ? <div className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase animate-pulse">Buscando no Questor...</div> :
                                         !(questorObras || []).length ? <div className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase">Nenhuma obra/CNO</div> :
                                         (questorObras || []).map(ob => (
                                            <button key={ob.codigooutemp} type="button" onClick={() => handlePickObra(ob)}
                                                className="w-full text-left px-3 py-2 text-[11px] text-[var(--v-text-bold)] hover:bg-[var(--v-accent)]/10 border-b border-white/5">
                                                {ob.nome} <span className="font-mono text-[var(--v-accent)]">— CNO {ob.cno || '—'}</span>
                                            </button>
                                         ))}
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Endereço <span className="text-[var(--v-accent)]">(layout DIMOB)</span>{enderecoForm.fonte !== 'MANUAL' && <span className="ml-2 text-[8px] bg-[var(--v-accent)]/10 border border-[#ff4d00]/20 px-1.5 py-0.5 rounded text-[var(--v-accent)]">preenchido do Questor</span>}</label>
                            <div className="grid grid-cols-6 gap-2">
                                <input value={enderecoForm.logradouro} onChange={(e) => setEnderecoForm({...enderecoForm, logradouro: e.target.value, fonte: 'MANUAL'})} placeholder="Logradouro" className="col-span-4 bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.numero} onChange={(e) => setEnderecoForm({...enderecoForm, numero: e.target.value, fonte: 'MANUAL'})} placeholder="Número" className="col-span-2 bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.complemento} onChange={(e) => setEnderecoForm({...enderecoForm, complemento: e.target.value, fonte: 'MANUAL'})} placeholder="Complemento" className="col-span-3 bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.bairro} onChange={(e) => setEnderecoForm({...enderecoForm, bairro: e.target.value, fonte: 'MANUAL'})} placeholder="Bairro" className="col-span-3 bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.cep} onChange={(e) => setEnderecoForm({...enderecoForm, cep: e.target.value, fonte: 'MANUAL'})} placeholder="CEP" className="col-span-2 bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.uf} onChange={(e) => setEnderecoForm({...enderecoForm, uf: e.target.value.toUpperCase().slice(0,2), fonte: 'MANUAL'})} placeholder="UF" className="col-span-1 bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50 uppercase" />
                                <input value={enderecoForm.codigo_munic} onChange={(e) => setEnderecoForm({...enderecoForm, codigo_munic: e.target.value, fonte: 'MANUAL'})} placeholder="Cód. Município" className="col-span-3 bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                            </div>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Metragem Total (m²)</label>
                                <input type="number" value={formData.metragem} onChange={(e) => setFormData({...formData, metragem: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Custo Orçado</label>
                                <input type="number" value={formData.custo} onChange={(e) => setFormData({...formData, custo: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Adere ao RET?</label>
                                <select value={formData.ret} onChange={(e) => setFormData({...formData, ret: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50">
                                    <option value="N">Não</option>
                                    <option value="S">Sim</option>
                                </select>
                            </div>
                            {formData.ret === 'S' && (
                                <div className="space-y-1">
                                    <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Data Inicial RET</label>
                                    <input type="date" value={formData.datainicioret || ''} onChange={(e) => setFormData({...formData, datainicioret: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                </div>
                            )}
                            {formData.ret === 'S' && (
                                <div className="space-y-1">
                                    <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Alíquota RET (%)</label>
                                    <input type="number" step="0.01" value={formData.aliqret || ''} onChange={(e) => setFormData({...formData, aliqret: e.target.value})} placeholder="4.00" className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                </div>
                            )}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Status da Obra</label>
                                <select value={formData.obra_concluida} onChange={(e) => setFormData({...formData, obra_concluida: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50">
                                    <option value="N">Em Obras</option>
                                    <option value="S">Concluído</option>
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Cadastro Ativo</label>
                                <select value={formData.ativo} onChange={(e) => setFormData({...formData, ativo: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50">
                                    <option value="S">Ativo (Permite Vendas)</option>
                                    <option value="N">Inativo (Bloqueado)</option>
                                </select>
                            </div>
                        </div>
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Data de Conclusão</label>
                            <input type="date" value={formData.data_conclusao} onChange={(e) => setFormData({...formData, data_conclusao: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                        </div>
                    </div>
                </div>
              )}

              {activeTab === 'questor' && (
                <div className="space-y-8 animate-in slide-in-from-right-2 duration-500">
                    <div className="bg-[var(--v-accent)]/5 border border-[#ff4d00]/20 p-4 rounded-[var(--v-radius)] flex items-start gap-4">
                        <AlertCircle className="text-[var(--v-accent)] shrink-0" size={18} />
                        <div>
                            <h4 className="text-[10px] font-black text-[var(--v-text-bold)] uppercase tracking-widest">Mapeamento Contábil Especial</h4>
                            <p className="text-[10px] text-[var(--v-text-muted)] leading-relaxed mt-1">Os campos abaixo definem o de-para automático entre os movimentos do Vulcano e o Plano de Contas Especial da empresa selecionada no Questor. Use o searchable select para localizar a conta analítica.</p>
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

                    <div className="pt-6 border-t border-white/5 space-y-6">
                        <div className="w-1/3 space-y-1">
                            <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Centro de Custo Questor</label>
                            <select value={formData.centro_custo} onChange={(e) => setFormData({...formData, centro_custo: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50">
                                <option value="0">Sem mapeamento</option>
                                {centrosCusto.map(cc => <option key={cc.id} value={cc.id}>{cc.id} - {cc.descricao}</option>)}
                            </select>
                        </div>
                        <div className="border-t border-white/5 pt-6">
                            <h4 className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest mb-4">Mapeamento de Históricos</h4>
                            <div className="grid grid-cols-4 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Venda</label>
                                <select value={formData.hist_venda} onChange={(e) => setFormData({...formData, hist_venda: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Recebimento</label>
                                <select value={formData.hist_recebimento} onChange={(e) => setFormData({...formData, hist_recebimento: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Distrato</label>
                                <select value={formData.hist_distrato} onChange={(e) => setFormData({...formData, hist_distrato: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none border-[#ff4d00]/30 bg-[#ff4d00]/5 hover:border-[#ff4d00]">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Variação</label>
                                <select value={formData.hist_variacao} onChange={(e) => setFormData({...formData, hist_variacao: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Adiantamento</label>
                                <select value={formData.hist_adiantamento} onChange={(e) => setFormData({...formData, hist_adiantamento: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Baixa Adi.</label>
                                <select value={formData.hist_baixaadi} onChange={(e) => setFormData({...formData, hist_baixaadi: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Apr. Custo</label>
                                <select value={formData.hist_aprcusto} onChange={(e) => setFormData({...formData, hist_aprcusto: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Despesa Trib.</label>
                                <select value={formData.hist_despesa} onChange={(e) => setFormData({...formData, hist_despesa: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Estorno Saldo/Rec.</label>
                                <select value={formData.hist_estorno_saldo} onChange={(e) => setFormData({...formData, hist_estorno_saldo: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Estorno Custo</label>
                                <select value={formData.hist_estorno_custo} onChange={(e) => setFormData({...formData, hist_estorno_custo: e.target.value})} className="w-full bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                </div>
              )}

              {activeTab === 'estrutura' && (
                <div className="space-y-8 animate-in zoom-in-95 duration-500">
                    {/* Importação via matrícula de incorporação */}
                    <div className="bg-[var(--v-accent)]/5 border border-[#ff4d00]/20 p-4 rounded-[var(--v-radius)] space-y-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <h4 className="text-[10px] font-black text-[var(--v-text-bold)] uppercase tracking-widest">Importar da Matrícula de Incorporação (PDF)</h4>
                                <p className="text-[10px] text-[var(--v-text-muted)] mt-1">A certidão de inteiro teor é lida pela IA em 3 leituras independentes com conferência e desempate; você revisa a prévia antes de gravar.</p>
                            </div>
                            <input ref={matriculaInputRef} type="file" accept=".pdf" className="hidden" onChange={(e) => handleUploadMatricula(e.target.files?.[0])} />
                            <button
                                onClick={() => matriculaInputRef.current?.click()}
                                disabled={matriculaLoading}
                                className="bg-[var(--v-accent)] text-black px-4 py-2 rounded-[var(--v-radius)] font-black text-[10px] uppercase tracking-widest flex items-center gap-2 hover:bg-white transition-all disabled:opacity-50 shrink-0"
                            >
                                {matriculaLoading ? <Loader2 size={14} className="animate-spin"/> : <Database size={14}/>}
                                {matriculaLoading ? 'Lendo (até ~5 min)...' : 'Enviar matrícula'}
                            </button>
                        </div>

                        {matriculaLoading && (
                            <p className="text-[10px] text-[var(--v-accent)] animate-pulse font-bold uppercase tracking-widest">Extraindo com IA: 3 leituras do cadastro + 3 da estrutura + desempates. Aguarde nesta tela.</p>
                        )}

                        {matriculaPreview && (
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4 text-[11px] text-[var(--v-text-bold)]">
                                    <div className="space-y-1">
                                        <p><span className="text-[var(--v-text-faint)]">Empreendimento:</span> <b>{matriculaPreview.empreendimento.nome || '—'}</b></p>
                                        <p><span className="text-[var(--v-text-faint)]">Matrícula:</span> {matriculaPreview.empreendimento.matricula_numero || '—'} · {matriculaPreview.empreendimento.cartorio || ''}</p>
                                        <p><span className="text-[var(--v-text-faint)]">Incorporadora:</span> {matriculaPreview.empreendimento.incorporadora_nome || '—'} {matriculaPreview.empreendimento.incorporadora_cnpj && `(${matriculaPreview.empreendimento.incorporadora_cnpj})`}</p>
                                        <p><span className="text-[var(--v-text-faint)]">Endereço:</span> {[matriculaPreview.empreendimento.endereco?.logradouro, matriculaPreview.empreendimento.endereco?.numero, matriculaPreview.empreendimento.endereco?.bairro, matriculaPreview.empreendimento.endereco?.cep, matriculaPreview.empreendimento.endereco?.uf].filter(Boolean).join(', ') || '—'}</p>
                                    </div>
                                    <div className="space-y-1">
                                        <p><span className="text-[var(--v-text-faint)]">Blocos:</span> {matriculaPreview.blocos.join(', ')}</p>
                                        <p><span className="text-[var(--v-text-faint)]">Unidades:</span> <b>{matriculaPreview.total_unidades}</b></p>
                                        <p><span className="text-[var(--v-text-faint)]">Σ fração ideal:</span> {matriculaPreview.conferencias.soma_fracao_ideal_pct}% {matriculaPreview.conferencias.fracao_fecha_100 ? '✓' : '⚠ não fecha 100%'}</p>
                                        {matriculaPreview.conferencias.corrigidas_no_desempate.length > 0 && (
                                            <p className="text-[var(--v-accent)]">⚙ {matriculaPreview.conferencias.corrigidas_no_desempate.length} unidade(s) resolvidas em leitura de desempate</p>
                                        )}
                                    </div>
                                </div>

                                {matriculaPreview.criticas && (
                                    <div className={`p-3 rounded text-[10.5px] space-y-1 border ${matriculaPreview.criticas.unidades?.ok && matriculaPreview.criticas.area_privativa?.ok ? 'bg-[#22c55e]/10 border-[#22c55e]/30' : 'bg-[#ff9500]/10 border-[#ff9500]/40'}`}>
                                        <p className="font-black uppercase text-[var(--v-text-bold)]">Crítica contra a matrícula</p>
                                        <p style={{ color: matriculaPreview.criticas.unidades?.ok ? '#22c55e' : '#ff9500' }}>
                                            {matriculaPreview.criticas.unidades?.ok ? '✓' : '⚠'} Unidades: <b>{matriculaPreview.criticas.unidades?.extraido}</b> extraídas × <b>{matriculaPreview.criticas.unidades?.declarado ?? 'não consta'}</b> declaradas na matrícula
                                        </p>
                                        <p style={{ color: matriculaPreview.criticas.area_privativa?.ok ? '#22c55e' : '#ff9500' }}>
                                            {matriculaPreview.criticas.area_privativa?.ok ? '✓' : '⚠'} Área privativa: Σ <b>{(matriculaPreview.criticas.area_privativa?.soma_extraida_m2 ?? 0).toLocaleString('pt-BR')} m²</b>
                                            {matriculaPreview.criticas.area_privativa?.soma_priv_total_m2 > (matriculaPreview.criticas.area_privativa?.soma_extraida_m2 ?? 0) && ` (c/ acessória ${matriculaPreview.criticas.area_privativa.soma_priv_total_m2.toLocaleString('pt-BR')} m²)`}
                                            {' '}× <b>{matriculaPreview.criticas.area_privativa?.declarado_m2 ? matriculaPreview.criticas.area_privativa.declarado_m2.toLocaleString('pt-BR') + ' m²' : 'não consta'}</b> declarada
                                            {matriculaPreview.criticas.area_privativa?.base_comparacao === 'privativa+acessoria' && ' — total declarado inclui as áreas acessórias das vagas'}
                                            {matriculaPreview.criticas.area_privativa?.diferenca_m2 != null && !matriculaPreview.criticas.area_privativa?.ok && ` (diferença ${matriculaPreview.criticas.area_privativa.diferenca_m2.toLocaleString('pt-BR')} m²)`}
                                        </p>
                                        <p className="text-[var(--v-text-faint)]">
                                            Por bloco: {Object.entries(matriculaPreview.criticas.unidades_por_bloco || {}).map(([b, n]) => `${b}: ${n}`).join(' · ')}
                                        </p>
                                        {!(matriculaPreview.criticas.unidades?.ok && matriculaPreview.criticas.area_privativa?.ok) && (
                                            <p className="text-[var(--v-text-faint)]">Use o chat abaixo para apontar o que falta (ex.: "faltam os aptos 401 e 501 do bloco C e suas vagas").</p>
                                        )}
                                    </div>
                                )}

                                {(Object.keys(matriculaPreview.conferencias.divergencias_cadastro || {}).length > 0 || matriculaPreview.unidades.some(u => u.divergente_conferir)) && (
                                    <div className="bg-[#ff3b30]/10 border border-[#ff3b30]/30 p-3 rounded text-[10px] text-[var(--v-text-bold)] space-y-1">
                                        <p className="font-black uppercase text-[#ff3b30]">Conferir antes de gravar:</p>
                                        {Object.entries(matriculaPreview.conferencias.divergencias_cadastro || {}).map(([campo, vars]) => (
                                            <p key={campo}>• {campo}: leituras divergiram — {Array.isArray(vars) ? vars.join(' | ') : String(vars)}</p>
                                        ))}
                                        {matriculaPreview.unidades.filter(u => u.divergente_conferir).slice(0, 10).map(u => (
                                            <p key={`${u.bloco}-${u.numero}`}>• {u.bloco} nº {u.numero}: leituras divergiram sem desempate — confira na matrícula</p>
                                        ))}
                                    </div>
                                )}

                                <div className="flex items-center gap-4 flex-wrap text-[10px] text-[var(--v-text-bold)]">
                                    <label className="flex items-center gap-2 uppercase font-bold text-[var(--v-text-faint)]">Metragem a gravar:
                                        <select value={metragemCampo} onChange={(e) => setMetragemCampo(e.target.value)} className="bg-black/40 border border-white/5 p-1.5 text-[10px] text-[var(--v-text-bold)] outline-none">
                                            <option value="area_privativa_m2">Área privativa</option>
                                            <option value="area_privativa_total_m2">Área privativa total (c/ acessória)</option>
                                            <option value="area_total_m2">Área real total (c/ comum)</option>
                                        </select>
                                    </label>
                                    <label className="flex items-center gap-2 uppercase font-bold text-[var(--v-text-faint)]">
                                        <input type="checkbox" checked={incluirVaga} onChange={(e) => setIncluirVaga(e.target.checked)} /> Incluir vaga na descrição
                                    </label>
                                    <button onClick={aplicarCadastroMatricula} className="px-3 py-1.5 bg-white/5 border border-white/10 rounded text-[10px] font-bold uppercase hover:bg-[var(--v-accent)]/15 text-[var(--v-accent)]">Usar endereço/nome no cadastro</button>
                                </div>

                                <div className="max-h-64 overflow-y-auto custom-scrollbar border border-white/5 rounded">
                                    <table className="w-full text-[10px] text-[var(--v-text-bold)]">
                                        <thead className="sticky top-0 bg-black/90">
                                            <tr className="text-[var(--v-text-faint)] uppercase text-left">
                                                <th className="p-2">Bloco</th><th className="p-2">Unidade</th><th className="p-2">Vaga</th>
                                                <th className="p-2 text-right">Priv. m²</th><th className="p-2 text-right">Priv. total m²</th>
                                                <th className="p-2 text-right">Total m²</th><th className="p-2 text-right">Fração %</th><th className="p-2"></th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {matriculaPreview.unidades.map(u => (
                                                <tr key={`${u.bloco}-${u.numero}`} className="border-t border-white/5">
                                                    <td className="p-1.5">{u.bloco}</td>
                                                    <td className="p-1.5 font-bold">{descricaoUnidadeMatricula(u)}</td>
                                                    <td className="p-1.5 text-[var(--v-text-faint)]">{u.vaga || '—'}</td>
                                                    <td className="p-1.5 text-right font-mono">{u.area_privativa_m2 ?? '—'}</td>
                                                    <td className="p-1.5 text-right font-mono">{u.area_privativa_total_m2 ?? '—'}</td>
                                                    <td className="p-1.5 text-right font-mono">{u.area_total_m2 ?? '—'}</td>
                                                    <td className="p-1.5 text-right font-mono">{u.fracao_ideal_pct ?? '—'}</td>
                                                    <td className="p-1.5">{u.divergente_conferir ? <span title="Leituras divergiram — conferir" className="text-[#ff3b30] font-black">⚠</span> : u.origem_chat ? <span title="Localizada via chat de conferência" className="text-[#22c55e]">🗨</span> : u.corrigida_chat ? <span title="Corrigida via chat de conferência" className="text-[#22c55e]">🗨</span> : u.corrigida_desempate ? <span title="Resolvida em leitura de desempate" className="text-[var(--v-accent)]">⚙</span> : ''}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {/* CHAT DE CONFERÊNCIA — o operador aponta, a IA busca no documento integral */}
                                <div className="border border-white/10 rounded p-3 space-y-2">
                                    <p className="text-[10px] font-black uppercase text-[var(--v-text-faint)]">Conferência assistida (busca no texto integral da matrícula)</p>
                                    {chatLog.map((c, i) => (
                                        <div key={i} className="text-[10.5px] space-y-1">
                                            <p className="text-[var(--v-accent)]">▸ {c.pergunta}</p>
                                            <p className="text-[var(--v-text-bold)]">{c.resposta}</p>
                                            {(c.adicionadas.length > 0 || c.corrigidas.length > 0) && (
                                                <p className="text-[#22c55e]">
                                                    {c.adicionadas.length > 0 && `+ ${c.adicionadas.length} unidade(s) incluída(s): ${c.adicionadas.join(', ')}. `}
                                                    {c.corrigidas.length > 0 && `⚙ ${c.corrigidas.length} corrigida(s): ${c.corrigidas.join(', ')}.`}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                    <div className="flex gap-2">
                                        <input value={chatMsg} onChange={(e) => setChatMsg(e.target.value)}
                                            onKeyDown={(e) => { if (e.key === 'Enter' && !chatBusy) enviarChatMatricula(); }}
                                            placeholder={matriculaPreview.sessao_id ? 'ex.: faltam os aptos 401 e 501 do bloco C e suas vagas' : 'sessão indisponível — refaça a extração'}
                                            disabled={!matriculaPreview.sessao_id || chatBusy}
                                            className="flex-1 bg-black/40 border border-white/10 p-2 text-[11px] text-[var(--v-text-bold)] outline-none focus:border-[var(--v-accent)]/50 rounded" />
                                        <button onClick={enviarChatMatricula} disabled={!matriculaPreview.sessao_id || chatBusy || !chatMsg.trim()}
                                            className="px-4 py-2 bg-white/5 border border-white/10 rounded text-[10px] font-bold uppercase hover:bg-[var(--v-accent)]/15 text-[var(--v-accent)] disabled:opacity-40 flex items-center gap-2">
                                            {chatBusy && <Loader2 size={11} className="animate-spin"/>}
                                            {chatBusy ? 'Verificando…' : 'Verificar na matrícula'}
                                        </button>
                                    </div>
                                </div>

                                <div className="flex justify-end gap-3">
                                    <button onClick={() => setMatriculaPreview(null)} className="px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-faint)] hover:bg-white/5 rounded">Descartar</button>
                                    <button onClick={handleGravarEstrutura} disabled={importandoEstrutura}
                                        className="bg-[var(--v-accent)] text-black px-5 py-2 rounded-[var(--v-radius)] font-black text-[10px] uppercase tracking-widest hover:bg-white transition-all disabled:opacity-50 flex items-center gap-2">
                                        {importandoEstrutura && <Loader2 size={12} className="animate-spin"/>}
                                        Gravar {matriculaPreview.total_unidades} unidades em {matriculaPreview.blocos.length} blocos
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Totalizador de áreas p/ conferência (Σ metragem das unidades) */}
                    {unidades.length > 0 && (() => {
                        const porBloco = {};
                        unidades.forEach(u => {
                            const b = blocos.find(x => x.id === u.id_bloco);
                            const nome = b ? b.nome : '?';
                            porBloco[nome] = porBloco[nome] || { qtd: 0, m2: 0 };
                            porBloco[nome].qtd += 1;
                            porBloco[nome].m2 += parseFloat(u.metragem) || 0;
                        });
                        const totalM2 = unidades.reduce((s, u) => s + (parseFloat(u.metragem) || 0), 0);
                        return (
                            <div className="bg-black/30 border border-white/5 rounded-[var(--v-radius)] p-3 flex flex-wrap items-center gap-x-6 gap-y-1">
                                <span className="text-[9px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Totais p/ conferência:</span>
                                {Object.entries(porBloco).map(([nome, t]) => (
                                    <span key={nome} className="text-[10px] font-mono text-[var(--v-text-muted)]">{nome}: <b className="text-[var(--v-text-bold)]">{t.qtd} un · {t.m2.toFixed(2)} m²</b></span>
                                ))}
                                <span className="text-[10px] font-mono text-[var(--v-accent)] ml-auto">GERAL: <b>{unidades.length} un · {totalM2.toFixed(2)} m²</b></span>
                                <button
                                    onClick={() => { setFormData({ ...formData, metragem: totalM2.toFixed(2) }); alert(`Metragem total do empreendimento atualizada para ${totalM2.toFixed(2)} m² (Σ das unidades). Salve para gravar.`); }}
                                    title="Preenche o campo Metragem Total (aba Dados Gerais) com a soma das áreas das unidades"
                                    className="px-2.5 py-1 bg-white/5 border border-white/10 rounded text-[9px] font-bold uppercase hover:bg-[var(--v-accent)]/15 text-[var(--v-accent)]">
                                    Usar como metragem total
                                </button>
                            </div>
                        );
                    })()}

                    <div className="grid grid-cols-12 gap-8">
                        {/* Blocos List */}
                        <div className="col-span-4 border-r border-white/5 pr-8 space-y-4">
                            <div className="flex items-center justify-between">
                                <h4 className="text-[10px] font-black text-[var(--v-accent)] uppercase tracking-widest flex items-center gap-2">
                                    <Layers size={14}/> Blocos Estruturais
                                </h4>
                                {blocos.length > 1 && (
                                    <button
                                        onClick={async () => {
                                            if (!confirm(`Excluir TODOS os ${blocos.length} blocos e suas ${unidades.length} unidades deste empreendimento?`)) return;
                                            for (const b of blocos) {
                                                await fetch(`${API_BASE}/api/vulcano/blocos/${b.id}`, { method: 'DELETE' });
                                            }
                                            fetchEstrutura(editingEmp.id);
                                        }}
                                        className="text-[9px] font-bold uppercase text-[#ff3b30]/70 hover:text-[#ff3b30] transition-colors">
                                        Excluir todos
                                    </button>
                                )}
                            </div>

                            <div className="flex gap-2">
                                <input
                                    value={newBlocoName}
                                    onChange={(e) => setNewBlocoName(e.target.value)}
                                    placeholder="Ex: Bloco A"
                                    className="flex-1 bg-black/40 border border-white/5 p-2 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50"
                                />
                                <button onClick={handleAddBloco} className="bg-white/5 p-2 text-[var(--v-accent)] border border-white/10 hover:bg-[var(--v-accent)] hover:text-black transition-all">
                                    <Plus size={16}/>
                                </button>
                            </div>

                            <div className="space-y-2">
                                {loadingEstrutura ? (
                                    <div className="py-10 text-center"><Loader2 className="animate-spin mx-auto text-[var(--v-text-faint)]"/></div>
                                ) : blocos.map(b => (
                                    <div key={b.id} className="group p-3 bg-white/5 border border-white/5 flex justify-between items-center hover:border-[#ff4d00]/30 transition-all">
                                        <div className="flex items-center gap-3">
                                            <span className="text-[10px] font-black text-[var(--v-text-faint)]">{b.id}</span>
                                            <span className="text-[11px] font-bold text-[var(--v-text-bold)] uppercase">{b.nome}</span>
                                        </div>
                                        <button onClick={() => handleDeleteEstrutura('bloco', b.id)} title="Excluir o bloco inteiro (com as unidades dele)" className="p-1 text-[var(--v-text-faint)] hover:text-[#ff3b30] transition-all"><Trash2 size={12}/></button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Unidades List */}
                        <div className="col-span-8 space-y-4">
                            <h4 className="text-[10px] font-black text-[var(--v-accent)] uppercase tracking-widest flex items-center gap-2">
                                <Home size={14}/> Unidades Imobiliárias
                            </h4>
                            
                            <div className="grid grid-cols-5 gap-2">
                                <select 
                                    value={newUnidade.id_bloco} 
                                    onChange={(e) => setNewUnidade({...newUnidade, id_bloco: e.target.value})}
                                    className="bg-black/40 border border-white/5 p-2 text-[10px] text-[var(--v-text-bold)] outline-none"
                                >
                                    <option value="">Bloco...</option>
                                    {blocos.map(b => <option key={b.id} value={b.id}>{b.nome}</option>)}
                                </select>
                                <input 
                                    placeholder="Nº Unidade" 
                                    value={newUnidade.descricao}
                                    onChange={(e) => setNewUnidade({...newUnidade, descricao: e.target.value})}
                                    className="bg-black/40 border border-white/5 p-2 text-[10px] text-[var(--v-text-bold)] outline-none"
                                />
                                <input 
                                    placeholder="Metragem" 
                                    type="number"
                                    value={newUnidade.metragem}
                                    onChange={(e) => setNewUnidade({...newUnidade, metragem: e.target.value})}
                                    className="bg-black/40 border border-white/5 p-2 text-[10px] text-[var(--v-text-bold)] outline-none"
                                />
                                <input 
                                    placeholder="Insc. Imob" 
                                    value={newUnidade.inscricao}
                                    onChange={(e) => setNewUnidade({...newUnidade, inscricao: e.target.value})}
                                    className="bg-black/40 border border-white/5 p-2 text-[10px] text-[var(--v-text-bold)] outline-none"
                                />
                                <button onClick={handleAddUnidade} className="bg-[var(--v-accent)]/10 text-[var(--v-accent)] border border-[#ff4d00]/30 py-2 text-[10px] font-black uppercase hover:bg-[var(--v-accent)] hover:text-black transition-all">Add</button>
                            </div>

                            <div className="bg-black/20 border border-white/5 rounded-[var(--v-radius)] overflow-hidden">
                                <table className="w-full text-left text-[10px]">
                                    <thead className="bg-white/5 text-[var(--v-text-faint)] font-black uppercase tracking-widest">
                                        <tr>
                                            <th className="p-3">Bloco</th>
                                            <th className="p-3">Descrição/Nº</th>
                                            <th className="p-3">Metragem</th>
                                            <th className="p-3">Inc. Questor</th>
                                            <th className="p-3">Situação</th>
                                            <th className="p-3 text-right">Ação</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {unidades.map(u => (
                                            <tr key={u.id} className="hover:bg-white/5 transition-colors">
                                                <td className="p-3 font-bold text-[var(--v-text-muted)]">{blocos.find(b => b.id === u.id_bloco)?.nome || u.id_bloco}</td>
                                                <td className="p-3 font-black text-[var(--v-text-bold)]">{u.descricao}</td>
                                                <td className="p-3 text-[var(--v-accent-3)] font-mono">{u.metragem} m²</td>
                                                <td className="p-3 text-[var(--v-text-faint)] font-mono">{u.inscricao || '---'}</td>
                                                <td className="p-3">
                                                    {u.vendida ? (
                                                        <span className="px-2 py-0.5 rounded font-black uppercase tracking-widest text-[9px]" style={{ background: 'rgba(255, 149, 0, 0.12)', border: '1px solid rgba(255, 149, 0, 0.4)', color: '#ff9500' }}>
                                                            Vendida · {u.data_venda}
                                                        </span>
                                                    ) : (
                                                        <span className="px-2 py-0.5 rounded font-black uppercase tracking-widest text-[9px]" style={{ background: 'rgba(34, 197, 94, 0.10)', border: '1px solid rgba(34, 197, 94, 0.35)', color: '#22c55e' }}>
                                                            Disponível
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="p-3 text-right">
                                                    {u.vendida ? (
                                                        <span title="Unidade com venda ativa — exclua ou distrate a venda antes" className="text-[var(--v-text-faint)] opacity-40 cursor-not-allowed inline-block"><Trash2 size={12}/></span>
                                                    ) : (
                                                        <button onClick={() => handleDeleteEstrutura('unidade', u.id)} className="text-[var(--v-text-faint)] hover:text-[#ff3b30] transition-colors"><Trash2 size={12}/></button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                        {!unidades.length && !loadingEstrutura && (
                                            <tr>
                                                <td colSpan="6" className="p-10 text-center text-[var(--v-text-faint)] font-black uppercase tracking-[0.3em]">Nenhuma unidade vinculada</td>
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
              <button onClick={() => setShowModal(false)} className="px-6 py-2.5 text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] transition-colors">Cancelar</button>
              <button 
                onClick={handleSave}
                className="px-8 py-2.5 bg-[var(--v-accent)] text-black font-black text-[10px] uppercase tracking-widest hover:bg-white transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(255,77,0,0.2)]"
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
