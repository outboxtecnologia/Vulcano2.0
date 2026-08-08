import React, { useState, useEffect } from 'react';
import { Users, Search, Plus, Pencil, Loader2 } from 'lucide-react';
import { API_BASE } from './apiBase';

// Tela de Clientes (Melhorias 2, item 4): o cliente continua nascendo dentro
// da venda; aqui o operador pesquisa a base toda, inclui avulso e corrige
// nome/documento. Tabela viva CLIENTE = ID / NOME / CNPJ apenas.
export const ClientesView = ({ selectedEmpresa }) => {
  const [busca, setBusca] = useState('');
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [buscou, setBuscou] = useState(false);
  const [modal, setModal] = useState(null); // { id?, nome, cpf_cnpj }
  const [salvando, setSalvando] = useState(false);

  const pesquisar = async (termo = busca) => {
    setLoading(true);
    try {
      const q = termo.trim()
        ? `busca=${encodeURIComponent(termo.trim())}&empresa_id=${selectedEmpresa || 0}`
        : `empresa_id=${selectedEmpresa || 0}`;
      const res = await fetch(`${API_BASE}/api/vulcano/clientes?${q}`);
      const d = await res.json();
      if (!res.ok) throw new Error(d?.detail || `HTTP ${res.status}`);
      setClientes(Array.isArray(d) ? d : []);
      setBuscou(true);
    } catch (e) {
      alert('Falha na busca: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (selectedEmpresa) pesquisar(''); }, [selectedEmpresa]);

  const salvar = async () => {
    const m = modal;
    if (!m) return;
    if (!m.nome.trim()) { alert('Informe o nome.'); return; }
    const dig = (m.cpf_cnpj || '').replace(/\D/g, '');
    if (dig.length !== 11 && dig.length !== 14) { alert('Documento deve ser CPF (11 dígitos) ou CNPJ (14).'); return; }
    setSalvando(true);
    try {
      const url = m.id ? `${API_BASE}/api/vulcano/clientes/${m.id}` : `${API_BASE}/api/vulcano/clientes`;
      const res = await fetch(url, {
        method: m.id ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: m.nome.trim(), cpf_cnpj: m.cpf_cnpj.trim() })
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d?.detail || `HTTP ${res.status}`);
      alert(d.message || 'Salvo.');
      setModal(null);
      pesquisar();
    } catch (e) {
      alert('Falha ao salvar: ' + e.message);
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-black uppercase tracking-widest flex items-center gap-3" style={{ color: 'var(--v-text-bold)' }}>
          <Users size={20} className="text-[var(--v-accent)]" /> Clientes
        </h2>
        <div className="flex gap-2 items-center">
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--v-text-faint)]" />
            <input value={busca} onChange={(e) => setBusca(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') pesquisar(); }}
              placeholder="Nome ou CPF/CNPJ (base toda)..."
              className="bg-[var(--v-bg)] border border-[var(--v-border)] pl-8 pr-3 py-2 text-xs rounded w-72 outline-none focus:border-[var(--v-accent)]/50" style={{ color: 'var(--v-text-bold)' }} />
          </div>
          <button onClick={() => pesquisar()} className="px-4 py-2 rounded text-[11px] font-bold uppercase tracking-widest bg-[var(--v-tint)] border border-[var(--v-border)] hover:bg-[var(--v-tint)]" style={{ color: 'var(--v-text-bold)' }}>
            Buscar
          </button>
          <button onClick={() => setModal({ nome: '', cpf_cnpj: '' })} className="flex items-center gap-2 px-4 py-2 rounded text-[11px] font-black uppercase tracking-widest bg-[var(--v-accent)] text-black hover:bg-white transition-all">
            <Plus size={13} /> Novo cliente
          </button>
        </div>
      </div>
      <p className="text-[10px]" style={{ color: 'var(--v-text-faint)' }}>
        No fluxo normal o cliente nasce dentro da venda (digite o CPF na Nova Venda e o cadastro é criado ao salvar).
        Esta tela serve para cadastro avulso e correção de nome/documento. Sem busca, lista os clientes com venda na empresa selecionada.
      </p>

      <div className="bg-[var(--v-tint)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden">
        <table className="w-full text-left text-[11px]">
          <thead className="bg-[var(--v-tint)] text-[var(--v-text-faint)] font-black uppercase tracking-widest text-[9.5px]">
            <tr>
              <th className="p-3 w-20">ID</th>
              <th className="p-3">Nome</th>
              <th className="p-3 w-52">CPF/CNPJ</th>
              <th className="p-3 w-16 text-right">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {loading && (
              <tr><td colSpan="4" className="p-8 text-center"><Loader2 size={16} className="animate-spin inline text-[var(--v-accent)]" /></td></tr>
            )}
            {!loading && clientes.map(c => (
              <tr key={c.id} className="hover:bg-[var(--v-tint)] transition-colors">
                <td className="p-3 font-mono text-[var(--v-text-faint)]">#{c.id}</td>
                <td className="p-3 font-bold" style={{ color: 'var(--v-text-bold)' }}>{c.nome || <span className="text-[var(--v-warn)]">(sem nome)</span>}</td>
                <td className="p-3 font-mono text-[var(--v-text-muted)]">{c.cpf_cnpj || '—'}</td>
                <td className="p-3 text-right">
                  <button onClick={() => setModal({ id: c.id, nome: c.nome || '', cpf_cnpj: c.cpf_cnpj || '' })}
                    title="Editar nome/documento" className="text-[var(--v-text-faint)] hover:text-[var(--v-accent)] transition-colors">
                    <Pencil size={13} />
                  </button>
                </td>
              </tr>
            ))}
            {!loading && buscou && !clientes.length && (
              <tr><td colSpan="4" className="p-10 text-center text-[var(--v-text-faint)] font-black uppercase tracking-[0.3em]">Nenhum cliente encontrado</td></tr>
            )}
          </tbody>
        </table>
        {clientes.length >= 100 && (
          <div className="px-3 py-1.5 text-[9px] uppercase tracking-widest" style={{ color: 'var(--v-text-faint)' }}>Mostrando os 100 primeiros — refine a busca</div>
        )}
      </div>

      {modal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[110] p-6">
          <div className="w-full max-w-md rounded-xl shadow-2xl flex flex-col p-6" style={{ background: 'var(--v-bg)', border: '1px solid var(--v-line-warm)' }}>
            <h3 className="text-lg font-black uppercase tracking-widest flex items-center gap-3 mb-4" style={{ color: 'var(--v-text-bold)' }}>
              <Users size={18} color="var(--v-accent)" /> <span>{modal.id ? `Editar cliente #${modal.id}` : 'Novo cliente'}</span>
            </h3>
            <div className="space-y-3 mb-6">
              <div>
                <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: 'var(--v-text-muted)' }}>Nome / Razão social</label>
                <input value={modal.nome} onChange={(e) => setModal({ ...modal, nome: e.target.value })} maxLength={100}
                  className="w-full p-2.5 rounded text-[12px] outline-none" style={{ background: 'var(--v-card)', border: '1px solid rgba(255, 160, 80, 0.08)', color: 'var(--v-text-bold)' }} />
              </div>
              <div>
                <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: 'var(--v-text-muted)' }}>CPF / CNPJ</label>
                <input value={modal.cpf_cnpj} onChange={(e) => setModal({ ...modal, cpf_cnpj: e.target.value })} maxLength={20}
                  placeholder="000.000.000-00 ou 00.000.000/0000-00"
                  className="w-full p-2.5 rounded text-[12px] outline-none font-mono" style={{ background: 'var(--v-card)', border: '1px solid rgba(255, 160, 80, 0.08)', color: 'var(--v-text-bold)' }} />
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setModal(null)} className="px-4 py-2 hover:bg-[var(--v-tint)] transition-colors text-[11px] font-bold uppercase tracking-widest rounded" style={{ color: 'var(--v-text-muted)' }}>Cancelar</button>
              <button onClick={salvar} disabled={salvando} className="px-6 py-2 rounded text-[11px] font-bold uppercase tracking-widest disabled:opacity-50" style={{ background: 'linear-gradient(135deg, var(--v-accent), var(--v-accent-2))', color: 'var(--v-accent-soft)' }}>
                {salvando ? 'Gravando…' : 'Salvar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
