import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { 
  Building2, Plus, Edit, Trash2, Search, X, Check, Loader2, 
  Settings, Database, Construction, Layers, Home, Ruler,
  ChevronRight, ArrowRight, Save, Info, AlertCircle
} from 'lucide-react';
import { API_BASE } from './apiBase';

// Estilo padrao dos campos do modal. As cores vem do tema: com bg-[var(--v-card)] fixo, nos
// temas LIGHT e NUMB o campo ficava escuro com texto quase preto dentro de um painel
// branco — formulario ilegivel.
const CAMPO = "w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[var(--v-accent)]/50";

// Base do formulario. Editar faz merge SOBRE isto ({...FORM_VAZIO, ...emp}) em vez de
// substituir o objeto: campo que a API nao devolve continua string/numero em vez de
// virar undefined, o que transformava o input em uncontrolled no meio da edicao.
const FORM_VAZIO = {
  nome: '', cnpj: '', cno: '', metragem: 0, custo: 0, endereco: '',
  ret: 'N', datainicioret: '', aliqret: 0,
  ativo: 'S', obra_concluida: 'N', data_conclusao: '',
  conta_caixa: 0, conta_clientes: 0, conta_adi_cli: 0, conta_estand: 0, conta_estcon: 0,
  conta_despesa: 0, conta_rec: 0, conta_variacao: 0, conta_devolucao: 0, centro_custo: 0,
  hist_venda: 0, hist_recebimento: 0, hist_variacao: 0, hist_baixaadi: 0,
  hist_estorno_saldo: 0, hist_adiantamento: 0, hist_aprcusto: 0, hist_despesa: 0,
  hist_estorno_custo: 0,
};

/** Erro do FastAPI em texto legivel: num 422 o detail e uma lista de objetos pydantic. */
function mensagemDeErro(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const campo = Array.isArray(d.loc) ? d.loc.filter((p) => p !== 'body').join('.') : '';
        return campo ? `${campo}: ${d.msg}` : d.msg;
      })
      .join('\n');
  }
  return fallback;
}

// A API devolve {"detail": "..."} nos erros 500 (ex.: Firebird fora do ar).
// Sem esta guarda o objeto de erro cai direto no estado e quebra o .map() na renderizacao.
const asArray = (v) => (Array.isArray(v) ? v : []);

export const EmpreendimentosView = ({ selectedEmpresa, onNavigate }) => {
  const [empreendimentos, setEmpreendimentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingEmp, setEditingEmp] = useState(null);
  // Empresa vigente quando o modal abriu. O submit grava NELA, nao na que estiver
  // selecionada no momento de salvar: abrir o cadastro na empresa A e trocar para B
  // antes de clicar em salvar reatribuia o empreendimento para B em silencio.
  const [modalEmpresaId, setModalEmpresaId] = useState(null);
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

  const [formData, setFormData] = useState(FORM_VAZIO);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Endereco estruturado (layout DIMOB) — persiste no banco proprio do app
  const EMPTY_ENDERECO = { tipo_logradouro: '', logradouro: '', numero: '', complemento: '', bairro: '', cep: '', uf: '', codigo_munic: '', fonte: 'MANUAL', codigo_outemp: null, codigo_estab: null };
  const [enderecoForm, setEnderecoForm] = useState(EMPTY_ENDERECO);

  useEffect(() => {
    const ac = new AbortController();
    fetchEmpreendimentos(ac.signal);
    // caches dos pickers sao por empresa — trocar de empresa invalida
    setQuestorEstabs(null);
    setQuestorObras(null);
    setPickerOpen(null);
    if (selectedEmpresa) {
        fetchQuestorData(ac.signal);
    }
    return () => ac.abort();
  }, [selectedEmpresa]);

  // guarda contra resposta stale do fetch de endereco (modal reaberto p/ outro emp)
  const enderecoReqRef = React.useRef(0);

  const fetchEmpreendimentos = async (signal) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`, { signal });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      setEmpreendimentos(asArray(data));
      setError(null);
      setLoading(false);
    } catch (err) {
      if (err.name === 'AbortError') return; // troca de empresa/desmonte: nao e falha
      setEmpreendimentos([]);
      setError("Falha ao comunicar com node Vulcano");
      setLoading(false);
    }
  };

  const fetchQuestorData = async (signal) => {
    setLoadingQuestor(true);
    try {
        const [pc, cc, hi] = await Promise.all([
            fetch(`${API_BASE}/api/questor/plano-contas-espec?empresa_id=${selectedEmpresa}`, { signal }).then(r => r.json()),
            fetch(`${API_BASE}/api/questor/centrocusto?empresa_id=${selectedEmpresa}`, { signal }).then(r => r.json()),
            fetch(`${API_BASE}/api/questor/historicos`, { signal }).then(r => r.json())
        ]);
        setPlanoContas(asArray(pc?.contas));
        setCentrosCusto(asArray(cc));
        setHistoricos(asArray(hi));
    } catch (e) {
        if (e.name === 'AbortError') return;
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
        const res = await fetch(`${API_BASE}/api/vulcano/empreendimentos/${empId}/detalhes`);
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
      // Merge sobre o formulario vazio: campo ausente na resposta da API mantem o
      // valor padrao em vez de virar undefined (input uncontrolled).
      setFormData({
        ...FORM_VAZIO,
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
      setFormData(FORM_VAZIO);
      setEnderecoForm(EMPTY_ENDERECO);
      setBlocos([]);
      setUnidades([]);
    }
    setSaveError(null);
    setModalEmpresaId(selectedEmpresa);
    setActiveTab('dados');
    setShowModal(true);
  };

  /** Fecha o modal e zera tudo: antes o estado sobrevivia para a proxima abertura. */
  const fecharModal = () => {
    setShowModal(false);
    setEditingEmp(null);
    setModalEmpresaId(null);
    setFormData(FORM_VAZIO);
    setEnderecoForm(EMPTY_ENDERECO);
    setBlocos([]);
    setUnidades([]);
    setNewBlocoName('');
    setNewUnidade({ id_bloco: '', descricao: '', metragem: '', inscricao: '' });
    setSaveError(null);
    setSaving(false);
    setPickerOpen(null);
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
    if (saving) return; // duplo clique criava dois registros: o id vem de MAX(ID)+1

    if (!String(formData.nome || '').trim()) {
      setSaveError('Informe o nome do empreendimento.');
      setActiveTab('dados');
      return;
    }

    const empresaDoModal = modalEmpresaId ?? selectedEmpresa;
    const method = editingEmp ? 'PATCH' : 'POST';
    const url = editingEmp
      ? `${API_BASE}/api/vulcano/empreendimentos/${editingEmp.id}`
      : `${API_BASE}/api/vulcano/empreendimentos?empresa_id=${empresaDoModal}`;

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
        empresa_id: parseInt(empresaDoModal),
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
        hist_baixaadi: parseInt(formData.hist_baixaadi || 0),
        hist_estorno_saldo: parseInt(formData.hist_estorno_saldo || 0),
        hist_adiantamento: parseInt(formData.hist_adiantamento || 0),
        hist_aprcusto: parseInt(formData.hist_aprcusto || 0),
        hist_despesa: parseInt(formData.hist_despesa || 0),
        hist_estorno_custo: parseInt(formData.hist_estorno_custo || 0)
    };

    setSaving(true);
    setSaveError(null);
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
        fecharModal();
        fetchEmpreendimentos();
        return;
      }
      // Corpo pode nao ser JSON (502/HTML de proxy): antes isso estourava aqui e caia
      // no catch, que reportava "Erro de rede" — mensagem enganosa.
      const errData = await res.json().catch(() => null);
      setSaveError(mensagemDeErro(errData?.detail, `Falha ao salvar (HTTP ${res.status}).`));
    } catch (err) {
      setSaveError(`Não foi possível falar com a API: ${err.message}`);
    } finally {
      setSaving(false);
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
    const selected = planoContas.find(c => String(c.id) === String(formData[name]));

    const displayValue = (() => {
        const val = String(formData[name] || '');
        if (/^\d+$/.test(val)) {
            const matched = planoContas.find(c => String(c.id) === val);
            if (matched) return `${matched.id} - ${matched.descricao}`;
        }
        return val;
    })();

    return (
      <div className="space-y-1">
        <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">{label}</label>
        <div className="relative group">
            <input
                list={listId}
                value={displayValue}
                onChange={(e) => setFormData({ ...formData, [name]: e.target.value })}
                className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50 transition-all font-mono"
                placeholder={loadingQuestor ? "Carregando..." : "Digite ou selecione..."}
            />
            <datalist id={listId}>
                {filtered.map(c => (
                    <option key={c.id} value={c.id}>{c.classificacao} - {c.descricao}</option>
                ))}
            </datalist>
            <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-20 group-hover:opacity-100 transition-opacity">
                <Search size={12} className="text-[var(--v-accent)]" />
            </div>
        </div>
        <p className="text-[9px] text-[var(--v-text-faint)] font-medium truncate" title={selected ? selected.descricao : ''}>
            Questor ID: {formData[name] || '0'} {selected ? `— ${selected.descricao}` : ''}
        </p>
      </div>
    );
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
      <div className="flex justify-between items-end border-b border-[var(--v-border)] pb-6">
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
              className="w-80 bg-[var(--v-card)] border border-[var(--v-border)] rounded-[var(--v-radius)] pl-9 pr-3 py-3 text-xs text-[var(--v-text-bold)] outline-none focus:border-[var(--v-accent)]/50 transition-all placeholder:text-[var(--v-text-faint)]"
            />
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="bg-[var(--v-accent)] text-[var(--v-text-inv)] px-6 py-3 rounded-[var(--v-radius)] font-black text-[10px] uppercase tracking-[0.2em] flex items-center gap-2 hover:bg-[var(--v-hover)] transition-all shadow-[0_0_20px_rgba(255,77,0,0.3)] group"
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
            <div className="p-6 bg-[var(--v-card)] backdrop-blur-md border border-[var(--v-border)] rounded-[var(--v-radius)] hover:border-[var(--v-accent)]/30 transition-all duration-300 flex flex-col h-full gap-4">
              <div className="flex justify-between items-start">
                <div className="w-10 h-10 bg-[var(--v-tint)] flex items-center justify-center rounded-[var(--v-radius)]">
                  <Building2 size={20} className={emp.ativo === 'N' ? "text-[var(--v-accent-3)]" : "text-[var(--v-accent)]"} />
                </div>
                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => handleOpenModal(emp)} className="p-2 bg-[var(--v-tint)] hover:bg-[rgb(var(--v-accent-rgb)_/_0.1)] hover:text-[var(--v-accent)] rounded-[var(--v-radius)] transition-colors"><Edit size={14}/></button>
                  <button onClick={() => handleDelete(emp.id)} className="p-2 bg-[var(--v-tint)] hover:bg-[var(--v-err)]/10 hover:text-[var(--v-err)] rounded-[var(--v-radius)] transition-colors"><Trash2 size={14}/></button>
                </div>
              </div>
              
              <div className="space-y-1">
                <h3 className="font-headline font-black text-[var(--v-text-bold)] uppercase tracking-wider text-sm">{emp.nome}</h3>
                <p className="text-[10px] text-[var(--v-text-faint)] font-bold uppercase py-1 border-b border-[var(--v-border)]">CNO: {emp.cno || 'Não Informado'}</p>
                <p className="text-[10px] text-[var(--v-text-faint)] font-bold uppercase py-1 border-b border-[var(--v-border)]">CNPJ: {emp.cnpj || '—'}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-2">
                <div className="space-y-1">
                  <span className="text-[9px] text-[var(--v-text-faint)] font-black uppercase tracking-widest block">Metragem</span>
                  <div className="flex items-center gap-1.5 text-[rgb(var(--v-text-bold-rgb)_/_0.8)] font-mono text-[11px]">
                    <Ruler size={12} className="text-[var(--v-accent)]" /> {emp.metragem || 0} m²
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-[9px] text-[var(--v-text-faint)] font-black uppercase tracking-widest block">Custo Orc.</span>
                  <div className="flex items-center gap-1.5 text-[rgb(var(--v-text-bold-rgb)_/_0.8)] font-mono text-[11px]">
                    <Database size={12} className="text-[var(--v-accent-3)]" /> {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(emp.custo || 0)}
                  </div>
                </div>
              </div>

              <div className="mt-auto pt-4 flex items-center justify-between">
                 <div className="flex gap-2">
                    {emp.ret === 'S' && <span className="text-[8px] bg-[rgb(var(--v-accent-rgb)_/_0.1)] text-[var(--v-accent)] border border-[var(--v-accent)]/20 px-1.5 py-0.5 rounded-[var(--v-radius)] font-black uppercase">RET</span>}
                    {emp.ativo === 'N' && <span className="text-[8px] bg-[var(--v-err)]/10 text-[var(--v-err)] border border-[var(--v-err)]/20 px-1.5 py-0.5 rounded-[var(--v-radius)] font-black uppercase">Inativo</span>}
                    {emp.obra_concluida === 'S' ? 
                       <span className="text-[8px] bg-[var(--v-ok)]/10 text-[var(--v-accent-3)] border border-[var(--v-ok)]/20 px-1.5 py-0.5 rounded-[var(--v-radius)] font-black uppercase">Concluído</span> :
                       <span className="text-[8px] bg-[var(--v-info)]/10 text-[var(--v-accent-4)] border border-[var(--v-info)]/20 px-1.5 py-0.5 rounded-[var(--v-radius)] font-black uppercase">Em Obras</span>
                    }
                 </div>
                 <div className="flex items-center gap-2">
                   <div className="text-[9px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">ID {emp.id}</div>
                   {onNavigate && (
                     <button
                       onClick={(e) => { e.stopPropagation(); onNavigate('custos', emp.id); }}
                       title="Abrir Fechamento de Custos deste empreendimento"
                       className="flex items-center gap-1 px-2 py-1 bg-[rgb(var(--v-accent-rgb)_/_0.1)] hover:bg-[rgb(var(--v-accent-rgb)_/_0.25)] border border-[var(--v-accent)]/20 rounded-[var(--v-radius)] text-[8px] font-black uppercase tracking-widest text-[var(--v-accent)] transition-all group-hover:opacity-100 opacity-60"
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

      {showModal && createPortal(
        // Portal para o body: o conteudo do shell fica dentro de um wrapper
        // `relative z-10` (layouts/EmpresaLayout.jsx), que abre um stacking context.
        // Renderizado ali dentro, nenhum z-index alcanca a sidebar (z-60) — o modal
        // aparecia ATRAS dela. Mesmo padrao ja usado em AuditoriaERPView.
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Cadastro de empreendimento">
          <div className="absolute inset-0 bg-[var(--v-overlay)] backdrop-blur-sm" onClick={fecharModal}></div>
          <div className="relative w-[95vw] max-w-[1600px] max-h-[95vh] bg-[var(--v-deep)] border border-[var(--v-border)] shadow-2xl flex flex-col overflow-hidden">

            {/* Header Modal */}
            <div className="p-6 border-b border-[var(--v-border)] flex justify-between items-center bg-[var(--v-card)]">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-[var(--v-accent)] text-[var(--v-text-inv)] flex items-center justify-center rounded-[var(--v-radius)]">
                  <Building2 size={24} />
                </div>
                <div>
                  <h3 className="font-headline text-xl font-black text-[var(--v-text-bold)] uppercase tracking-tight">
                    {editingEmp ? 'Editar Empreendimento' : 'Novo Empreendimento'}
                  </h3>
                  <p className="text-[10px] text-[var(--v-text-faint)] font-black uppercase tracking-widest">Configuração de Parâmetros e Mapeamento</p>
                </div>
              </div>
              <button onClick={fecharModal} title="Fechar" aria-label="Fechar" className="text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] transition-colors p-2">
                <X size={24} />
              </button>
            </div>

            {/* Modal Tabs */}
            <div className="flex border-b border-[var(--v-border)] bg-[rgb(var(--v-card-rgb)_/_0.5)]">
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
                            ? 'text-[var(--v-accent)] border-[var(--v-accent)] bg-[rgb(var(--v-accent-rgb)_/_0.05)]' 
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
                            <label htmlFor="emp-nome" className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">
                              Nome do Empreendimento <span className="text-[var(--v-accent)]">*</span>
                            </label>
                            <input
                              id="emp-nome"
                              autoFocus
                              value={formData.nome}
                              onChange={(e) => { setFormData({...formData, nome: e.target.value}); if (saveError) setSaveError(null); }}
                              className={CAMPO} />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1 relative">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">CNPJ RET</label>
                                <div className="flex gap-1">
                                    <input value={formData.cnpj} onChange={(e) => setFormData({...formData, cnpj: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                    <button type="button" onClick={() => handleOpenPicker('cnpj')} title="Puxar do Questor (estabelecimentos da empresa)"
                                        className="px-2.5 bg-[var(--v-tint)] hover:bg-[var(--v-accent)]/15 border border-[var(--v-border)] rounded-[var(--v-radius)] text-[var(--v-accent)] transition-colors shrink-0">
                                        <Database size={14}/>
                                    </button>
                                </div>
                                {pickerOpen === 'cnpj' && (
                                    <div className="absolute z-30 top-full left-0 right-0 mt-1 max-h-56 overflow-y-auto bg-[var(--v-shell)] border border-[var(--v-border)] rounded-[var(--v-radius)] shadow-2xl custom-scrollbar">
                                        {loadingPicker ? <div className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase animate-pulse">Buscando no Questor...</div> :
                                         !(questorEstabs || []).length ? <div className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase">Nenhum estabelecimento</div> :
                                         (questorEstabs || []).map(es => (
                                            <button key={es.codigoestab} type="button" onClick={() => handlePickEstab(es)}
                                                className="w-full text-left px-3 py-2 text-[11px] text-[var(--v-text-bold)] hover:bg-[var(--v-accent)]/10 border-b border-[var(--v-border)] font-mono">
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
                                    <input value={formData.cno} onChange={(e) => setFormData({...formData, cno: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                    <button type="button" onClick={() => handleOpenPicker('cno')} title="Puxar do Questor (obras/CNO da empresa)"
                                        className="px-2.5 bg-[var(--v-tint)] hover:bg-[var(--v-accent)]/15 border border-[var(--v-border)] rounded-[var(--v-radius)] text-[var(--v-accent)] transition-colors shrink-0">
                                        <Database size={14}/>
                                    </button>
                                </div>
                                {pickerOpen === 'cno' && (
                                    <div className="absolute z-30 top-full left-0 right-0 mt-1 max-h-56 overflow-y-auto bg-[var(--v-shell)] border border-[var(--v-border)] rounded-[var(--v-radius)] shadow-2xl custom-scrollbar">
                                        {loadingPicker ? <div className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase animate-pulse">Buscando no Questor...</div> :
                                         !(questorObras || []).length ? <div className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase">Nenhuma obra/CNO</div> :
                                         (questorObras || []).map(ob => (
                                            <button key={ob.codigooutemp} type="button" onClick={() => handlePickObra(ob)}
                                                className="w-full text-left px-3 py-2 text-[11px] text-[var(--v-text-bold)] hover:bg-[var(--v-accent)]/10 border-b border-[var(--v-border)]">
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
                                <input value={enderecoForm.logradouro} onChange={(e) => setEnderecoForm({...enderecoForm, logradouro: e.target.value, fonte: 'MANUAL'})} placeholder="Logradouro" className="col-span-4 bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.numero} onChange={(e) => setEnderecoForm({...enderecoForm, numero: e.target.value, fonte: 'MANUAL'})} placeholder="Número" className="col-span-2 bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.complemento} onChange={(e) => setEnderecoForm({...enderecoForm, complemento: e.target.value, fonte: 'MANUAL'})} placeholder="Complemento" className="col-span-3 bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.bairro} onChange={(e) => setEnderecoForm({...enderecoForm, bairro: e.target.value, fonte: 'MANUAL'})} placeholder="Bairro" className="col-span-3 bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.cep} onChange={(e) => setEnderecoForm({...enderecoForm, cep: e.target.value, fonte: 'MANUAL'})} placeholder="CEP" className="col-span-2 bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                                <input value={enderecoForm.uf} onChange={(e) => setEnderecoForm({...enderecoForm, uf: e.target.value.toUpperCase().slice(0,2), fonte: 'MANUAL'})} placeholder="UF" className="col-span-1 bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50 uppercase" />
                                <input value={enderecoForm.codigo_munic} onChange={(e) => setEnderecoForm({...enderecoForm, codigo_munic: e.target.value, fonte: 'MANUAL'})} placeholder="Cód. Município" className="col-span-3 bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                            </div>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Metragem Total (m²)</label>
                                <input type="number" value={formData.metragem} onChange={(e) => setFormData({...formData, metragem: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Custo Orçado</label>
                                <input type="number" value={formData.custo} onChange={(e) => setFormData({...formData, custo: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                            </div>
                        </div>
                        {/* Um grid so para os tres selects. Antes havia um grid-cols-2
                            aberto dentro de outro, o que dava 50% ao RET e espremia
                            Status e Ativo em 25% cada, truncando o texto das opcoes. */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Adere ao RET?</label>
                                <select value={formData.ret} onChange={(e) => setFormData({...formData, ret: e.target.value})} className={CAMPO}>
                                    <option value="N">Não</option>
                                    <option value="S">Sim</option>
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Status da Obra</label>
                                <select value={formData.obra_concluida} onChange={(e) => setFormData({...formData, obra_concluida: e.target.value})} className={CAMPO}>
                                    <option value="N">Em Obras</option>
                                    <option value="S">Concluído</option>
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Cadastro Ativo</label>
                                <select value={formData.ativo} onChange={(e) => setFormData({...formData, ativo: e.target.value})} className={CAMPO}>
                                    <option value="S">Ativo (Permite Vendas)</option>
                                    <option value="N">Inativo (Bloqueado)</option>
                                </select>
                            </div>
                        </div>
                        {/* Campos do RET em linha propria: so aparecem quando adere,
                            e sem aninhar grid dentro de grid. */}
                        {formData.ret === 'S' && (
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Data Inicial RET</label>
                                    <input type="date" value={formData.datainicioret || ''} onChange={(e) => setFormData({...formData, datainicioret: e.target.value})} className={CAMPO} />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Alíquota RET (%)</label>
                                    <input type="number" step="0.01" value={formData.aliqret || ''} onChange={(e) => setFormData({...formData, aliqret: e.target.value})} placeholder="4.00" className={CAMPO} />
                                </div>
                            </div>
                        )}
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Data de Conclusão</label>
                            <input type="date" value={formData.data_conclusao} onChange={(e) => setFormData({...formData, data_conclusao: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50" />
                        </div>
                    </div>
                </div>
              )}

              {activeTab === 'questor' && (
                <div className="space-y-8 animate-in slide-in-from-right-2 duration-500">
                    <div className="bg-[rgb(var(--v-accent-rgb)_/_0.05)] border border-[var(--v-accent)]/20 p-4 rounded-[var(--v-radius)] flex items-start gap-4">
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

                    <div className="pt-6 border-t border-[var(--v-border)] space-y-6">
                        <div className="w-1/3 space-y-1">
                            <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Centro de Custo Questor</label>
                            <select value={formData.centro_custo} onChange={(e) => setFormData({...formData, centro_custo: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2.5 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50">
                                <option value="0">Sem mapeamento</option>
                                {centrosCusto.map(cc => <option key={cc.id} value={cc.id}>{cc.id} - {cc.descricao}</option>)}
                            </select>
                        </div>
                        <div className="border-t border-[var(--v-border)] pt-6">
                            <h4 className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest mb-4">Mapeamento de Históricos</h4>
                            <div className="grid grid-cols-4 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Venda</label>
                                <select value={formData.hist_venda} onChange={(e) => setFormData({...formData, hist_venda: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Recebimento</label>
                                <select value={formData.hist_recebimento} onChange={(e) => setFormData({...formData, hist_recebimento: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            {/* Sem "Hist. Distrato": nao existe coluna para grava-lo em
                                EMPREENDIMENTO. O distrato e tratado pela tabela DISTRATOCTB
                                e pelos campos DISTRATO/DATADISTRATO de VENDA. O select
                                aceitava a escolha e a descartava em silencio. */}
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Variação</label>
                                <select value={formData.hist_variacao} onChange={(e) => setFormData({...formData, hist_variacao: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Adiantamento</label>
                                <select value={formData.hist_adiantamento} onChange={(e) => setFormData({...formData, hist_adiantamento: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Baixa Adi.</label>
                                <select value={formData.hist_baixaadi} onChange={(e) => setFormData({...formData, hist_baixaadi: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Apr. Custo</label>
                                <select value={formData.hist_aprcusto} onChange={(e) => setFormData({...formData, hist_aprcusto: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Hist. Despesa Trib.</label>
                                <select value={formData.hist_despesa} onChange={(e) => setFormData({...formData, hist_despesa: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Estorno Saldo/Rec.</label>
                                <select value={formData.hist_estorno_saldo} onChange={(e) => setFormData({...formData, hist_estorno_saldo: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none">
                                    <option value="0">Selecione...</option>
                                    {historicos.map(h => <option key={h.id} value={h.id}>{h.id} - {h.descricao}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Estorno Custo</label>
                                <select value={formData.hist_estorno_custo} onChange={(e) => setFormData({...formData, hist_estorno_custo: e.target.value})} className="w-full bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none">
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
                                {/* Icone e rotulo em spans proprios: ver comentario no botao Salvar. */}
                                <span className="inline-flex">{matriculaLoading ? <Loader2 size={14} className="animate-spin"/> : <Database size={14}/>}</span>
                                <span>{matriculaLoading ? 'Lendo (até ~5 min)...' : 'Enviar matrícula'}</span>
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
                                    <div className={`p-3 rounded text-[10.5px] space-y-1 border ${matriculaPreview.criticas.unidades?.ok && matriculaPreview.criticas.area_privativa?.ok ? 'bg-[var(--v-ok)]/10 border-[var(--v-ok)]/30' : 'bg-[var(--v-warn)]/10 border-[var(--v-warn)]/40'}`}>
                                        <p className="font-black uppercase text-[var(--v-text-bold)]">Crítica contra a matrícula</p>
                                        <p style={{ color: matriculaPreview.criticas.unidades?.ok ? 'var(--v-ok)' : 'var(--v-warn)' }}>
                                            {matriculaPreview.criticas.unidades?.ok ? '✓' : '⚠'} Unidades: <b>{matriculaPreview.criticas.unidades?.extraido}</b> extraídas × <b>{matriculaPreview.criticas.unidades?.declarado ?? 'não consta'}</b> declaradas na matrícula
                                        </p>
                                        <p style={{ color: matriculaPreview.criticas.area_privativa?.ok ? 'var(--v-ok)' : 'var(--v-warn)' }}>
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
                                    <div className="bg-[var(--v-err)]/10 border border-[var(--v-err)]/30 p-3 rounded text-[10px] text-[var(--v-text-bold)] space-y-1">
                                        <p className="font-black uppercase text-[var(--v-err)]">Conferir antes de gravar:</p>
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
                                        <select value={metragemCampo} onChange={(e) => setMetragemCampo(e.target.value)} className="bg-black/40 border border-[var(--v-line)] p-1.5 text-[10px] text-[var(--v-text-bold)] outline-none">
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

                                <div className="max-h-64 overflow-y-auto custom-scrollbar border border-[var(--v-line)] rounded">
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
                                                <tr key={`${u.bloco}-${u.numero}`} className="border-t border-[var(--v-line)]">
                                                    <td className="p-1.5">{u.bloco}</td>
                                                    <td className="p-1.5 font-bold">{descricaoUnidadeMatricula(u)}</td>
                                                    <td className="p-1.5 text-[var(--v-text-faint)]">{u.vaga || '—'}</td>
                                                    <td className="p-1.5 text-right font-mono">{u.area_privativa_m2 ?? '—'}</td>
                                                    <td className="p-1.5 text-right font-mono">{u.area_privativa_total_m2 ?? '—'}</td>
                                                    <td className="p-1.5 text-right font-mono">{u.area_total_m2 ?? '—'}</td>
                                                    <td className="p-1.5 text-right font-mono">{u.fracao_ideal_pct ?? '—'}</td>
                                                    <td className="p-1.5">{u.divergente_conferir ? <span title="Leituras divergiram — conferir" className="text-[var(--v-err)] font-black">⚠</span> : u.origem_chat ? <span title="Localizada via chat de conferência" className="text-[var(--v-ok)]">🗨</span> : u.corrigida_chat ? <span title="Corrigida via chat de conferência" className="text-[var(--v-ok)]">🗨</span> : u.corrigida_desempate ? <span title="Resolvida em leitura de desempate" className="text-[var(--v-accent)]">⚙</span> : ''}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {/* CHAT DE CONFERÊNCIA — o operador aponta, a IA busca no documento integral */}
                                <div className="border border-[var(--v-border)] rounded p-3 space-y-2">
                                    <p className="text-[10px] font-black uppercase text-[var(--v-text-faint)]">Conferência assistida (busca no texto integral da matrícula)</p>
                                    {chatLog.map((c, i) => (
                                        <div key={i} className="text-[10.5px] space-y-1">
                                            <p className="text-[var(--v-accent)]">▸ {c.pergunta}</p>
                                            <p className="text-[var(--v-text-bold)]">{c.resposta}</p>
                                            {(c.adicionadas.length > 0 || c.corrigidas.length > 0) && (
                                                <p className="text-[var(--v-ok)]">
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
                                            className="flex-1 bg-[var(--v-bg)] border border-[var(--v-border)] p-2 text-[11px] text-[var(--v-text-bold)] outline-none focus:border-[var(--v-accent)]/50 rounded" />
                                        <button onClick={enviarChatMatricula} disabled={!matriculaPreview.sessao_id || chatBusy || !chatMsg.trim()}
                                            className="px-4 py-2 bg-[var(--v-tint)] border border-[var(--v-border)] rounded text-[10px] font-bold uppercase hover:bg-[var(--v-accent)]/15 text-[var(--v-accent)] disabled:opacity-40 flex items-center gap-2">
                                            {chatBusy && <Loader2 size={11} className="animate-spin"/>}
                                            {chatBusy ? 'Verificando…' : 'Verificar na matrícula'}
                                        </button>
                                    </div>
                                </div>

                                <div className="flex justify-end gap-3">
                                    <button onClick={() => setMatriculaPreview(null)} className="px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-faint)] hover:bg-[var(--v-tint)] rounded">Descartar</button>
                                    <button onClick={handleGravarEstrutura} disabled={importandoEstrutura}
                                        className="bg-[var(--v-accent)] text-black px-5 py-2 rounded-[var(--v-radius)] font-black text-[10px] uppercase tracking-widest hover:bg-white transition-all disabled:opacity-50 flex items-center gap-2">
                                        {/* Idem: o spinner entra ANTES do rotulo, entao o rotulo precisa
                                            do span proprio para nao servir de no de referencia. */}
                                        {importandoEstrutura && <Loader2 size={12} className="animate-spin"/>}
                                        <span>Gravar {matriculaPreview.total_unidades} unidades em {matriculaPreview.blocos.length} blocos</span>
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
                            <div className="bg-[var(--v-scrim)] border border-[var(--v-line)] rounded-[var(--v-radius)] p-3 flex flex-wrap items-center gap-x-6 gap-y-1">
                                <span className="text-[9px] font-black text-[var(--v-text-faint)] uppercase tracking-widest">Totais p/ conferência:</span>
                                {Object.entries(porBloco).map(([nome, t]) => (
                                    <span key={nome} className="text-[10px] font-mono text-[var(--v-text-muted)]">{nome}: <b className="text-[var(--v-text-bold)]">{t.qtd} un · {t.m2.toFixed(2)} m²</b></span>
                                ))}
                                <span className="text-[10px] font-mono text-[var(--v-accent)] ml-auto">GERAL: <b>{unidades.length} un · {totalM2.toFixed(2)} m²</b></span>
                                <button
                                    onClick={() => { setFormData({ ...formData, metragem: totalM2.toFixed(2) }); alert(`Metragem total do empreendimento atualizada para ${totalM2.toFixed(2)} m² (Σ das unidades). Salve para gravar.`); }}
                                    title="Preenche o campo Metragem Total (aba Dados Gerais) com a soma das áreas das unidades"
                                    className="px-2.5 py-1 bg-[var(--v-tint)] border border-[var(--v-border)] rounded text-[9px] font-bold uppercase hover:bg-[var(--v-accent)]/15 text-[var(--v-accent)]">
                                    Usar como metragem total
                                </button>
                            </div>
                        );
                    })()}

                    <div className="grid grid-cols-12 gap-8">
                        {/* Blocos List */}
                        <div className="col-span-4 border-r border-[var(--v-border)] pr-8 space-y-4">
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
                                        className="text-[9px] font-bold uppercase text-[var(--v-err)]/70 hover:text-[var(--v-err)] transition-colors">
                                        Excluir todos
                                    </button>
                                )}
                            </div>

                            <div className="flex gap-2">
                                <input
                                    value={newBlocoName}
                                    onChange={(e) => setNewBlocoName(e.target.value)}
                                    placeholder="Ex: Bloco A"
                                    className="flex-1 bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#ff4d00]/50"
                                />
                                <button onClick={handleAddBloco} className="bg-[var(--v-tint)] p-2 text-[var(--v-accent)] border border-[var(--v-line)] hover:bg-[var(--v-accent)] hover:text-[var(--v-text-inv)] transition-all">
                                    <Plus size={16}/>
                                </button>
                            </div>

                            <div className="space-y-2">
                                {loadingEstrutura ? (
                                    <div className="py-10 text-center"><Loader2 className="animate-spin mx-auto text-[var(--v-text-faint)]"/></div>
                                ) : blocos.map(b => (
                                    <div key={b.id} className="group p-3 bg-[var(--v-tint)] border border-[var(--v-border)] flex justify-between items-center hover:border-[var(--v-accent)]/30 transition-all">
                                        <div className="flex items-center gap-3">
                                            <span className="text-[10px] font-black text-[var(--v-text-faint)]">{b.id}</span>
                                            <span className="text-[11px] font-bold text-[var(--v-text-bold)] uppercase">{b.nome}</span>
                                        </div>
                                        <button onClick={() => handleDeleteEstrutura('bloco', b.id)} title="Excluir o bloco inteiro (com as unidades dele)" className="p-1 text-[var(--v-text-faint)] hover:text-[var(--v-err)] transition-all"><Trash2 size={12}/></button>
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
                                    className="bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-[10px] text-[var(--v-text-bold)] outline-none"
                                >
                                    <option value="">Bloco...</option>
                                    {blocos.map(b => <option key={b.id} value={b.id}>{b.nome}</option>)}
                                </select>
                                <input 
                                    placeholder="Nº Unidade" 
                                    value={newUnidade.descricao}
                                    onChange={(e) => setNewUnidade({...newUnidade, descricao: e.target.value})}
                                    className="bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-[10px] text-[var(--v-text-bold)] outline-none"
                                />
                                <input 
                                    placeholder="Metragem" 
                                    type="number"
                                    value={newUnidade.metragem}
                                    onChange={(e) => setNewUnidade({...newUnidade, metragem: e.target.value})}
                                    className="bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-[10px] text-[var(--v-text-bold)] outline-none"
                                />
                                <input 
                                    placeholder="Insc. Imob" 
                                    value={newUnidade.inscricao}
                                    onChange={(e) => setNewUnidade({...newUnidade, inscricao: e.target.value})}
                                    className="bg-[var(--v-card)] border border-[var(--v-border)] p-2 text-[10px] text-[var(--v-text-bold)] outline-none"
                                />
                                <button onClick={handleAddUnidade} className="bg-[rgb(var(--v-accent-rgb)_/_0.1)] text-[var(--v-accent)] border border-[var(--v-accent)]/30 py-2 text-[10px] font-black uppercase hover:bg-[var(--v-accent)] hover:text-[var(--v-text-inv)] transition-all">Add</button>
                            </div>

                            <div className="bg-[var(--v-zebra)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden">
                                <table className="w-full text-left text-[10px]">
                                    <thead className="bg-[var(--v-tint)] text-[var(--v-text-faint)] font-black uppercase tracking-widest">
                                        <tr>
                                            <th className="p-3">Bloco</th>
                                            <th className="p-3">Descrição/Nº</th>
                                            <th className="p-3">Metragem</th>
                                            <th className="p-3">Inc. Questor</th>
                                            <th className="p-3 text-right">Ação</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[var(--v-line)]">
                                        {unidades.map(u => (
                                            <tr key={u.id} className="hover:bg-[var(--v-tint)] transition-colors">
                                                <td className="p-3 font-bold text-[var(--v-text-muted)]">{blocos.find(b => b.id === u.id_bloco)?.nome || u.id_bloco}</td>
                                                <td className="p-3 font-black text-[var(--v-text-bold)]">{u.descricao}</td>
                                                <td className="p-3 text-[var(--v-accent-3)] font-mono">{u.metragem} m²</td>
                                                <td className="p-3 text-[var(--v-text-faint)] font-mono">{u.inscricao || '---'}</td>
                                                <td className="p-3 text-right">
                                                    <button onClick={() => handleDeleteEstrutura('unidade', u.id)} className="text-[var(--v-text-faint)] hover:text-[var(--v-err)] transition-colors"><Trash2 size={12}/></button>
                                                </td>
                                            </tr>
                                        ))}
                                        {!unidades.length && !loadingEstrutura && (
                                            <tr>
                                                <td colSpan="5" className="p-10 text-center text-[var(--v-text-faint)] font-black uppercase tracking-[0.3em]">Nenhuma unidade vinculada</td>
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
            <div className="p-6 border-t border-[var(--v-border)] bg-[var(--v-card)] flex justify-between items-center gap-4">
              <div className="flex-1">
                {saveError && (
                  <p className="text-[11px] font-bold text-[var(--v-error)] flex items-start gap-2">
                    <AlertCircle size={14} className="shrink-0 mt-px" />
                    <span className="whitespace-pre-line">{saveError}</span>
                  </p>
                )}
              </div>
              <div className="flex gap-4 shrink-0">
                <button onClick={fecharModal} disabled={saving} className="px-6 py-2.5 text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] transition-colors disabled:opacity-40">Cancelar</button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-8 py-2.5 bg-[var(--v-accent)] text-[var(--v-text-inv)] font-black text-[10px] uppercase tracking-widest hover:bg-[var(--v-hover)] transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(255,77,0,0.2)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {/* O rotulo fica num <span> proprio de proposito. Como texto solto ele
                      vira irmao direto do icone, e trocar o icone no clique obriga o React
                      a um insertBefore usando esse no de texto como referencia. Basta que
                      algo externo (tradutor de pagina, leitor de tela) tenha embrulhado o
                      texto para o no deixar de ser filho do botao e o commit estourar com
                      "insertBefore ... is not a child of this node", derrubando a tela.
                      Com o span, o React troca o conteudo dele por textContent e nao
                      depende mais de quem e irmao de quem. */}
                  <span className="inline-flex">{saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}</span>
                  <span>{saving ? 'Salvando…' : 'Salvar Alterações'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};
