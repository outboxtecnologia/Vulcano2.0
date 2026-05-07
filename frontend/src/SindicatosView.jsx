import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw, ExternalLink, AlertTriangle,
  CheckCircle2, Clock, FileX, ChevronDown, ChevronUp
} from 'lucide-react';
import { API_BASE } from './apiBase';

const MESES = [
  '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
];

function StatusBadge({ status }) {
  const map = {
    ok: {
      icon: <CheckCircle2 size={11} />,
      label: 'Atualizado',
      cls: 'text-[var(--v-accent-3)] border-[#34c759]/30 bg-[#34c759]/10',
    },
    pendente: {
      icon: <Clock size={11} className="animate-pulse" />,
      label: 'Buscando CCT...',
      cls: 'text-[var(--v-accent-6)] border-[#ffcc00]/30 bg-[#ffcc00]/10',
    },
    erro: {
      icon: <AlertTriangle size={11} />,
      label: 'Erro',
      cls: 'text-[var(--v-accent)] border-[#ff4d00]/30 bg-[var(--v-accent)]/10',
    },
    pdf_nao_encontrado: {
      icon: <FileX size={11} />,
      label: 'CCT não encontrada',
      cls: 'text-[var(--v-text-faint)] border-[#666]/30 bg-[#666]/10',
    },
  };
  const cfg = map[status] || map.pendente;
  return (
    <span
      className={`flex items-center gap-1 text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded-[var(--v-radius)] border ${cfg.cls}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function ClausulaExpand({ texto }) {
  const [aberto, setAberto] = useState(false);
  if (!texto) return null;
  const curto = texto.slice(0, 120);
  return (
    <div className="mt-1">
      <p className="text-[10px] text-[var(--v-text-faint)] italic leading-relaxed">
        &ldquo;{aberto ? texto : curto}
        {!aberto && texto.length > 120 ? '...' : ''}&rdquo;
      </p>
      {texto.length > 120 && (
        <button
          onClick={() => setAberto((v) => !v)}
          className="flex items-center gap-1 text-[9px] text-[var(--v-accent)]/50 hover:text-[var(--v-accent)] mt-1 transition-colors"
        >
          {aberto ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
          {aberto ? 'Menos' : 'Ver trecho completo'}
        </button>
      )}
    </div>
  );
}

function InfoRow({ label, valor, clausula }) {
  return (
    <div className="py-2 border-b border-white/5 last:border-0">
      <div className="flex justify-between items-start gap-2">
        <span className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)] shrink-0">
          {label}
        </span>
        <span className="text-[11px] font-bold text-[var(--v-text-bold)] text-right">
          {valor || <span className="text-[#333] italic font-normal">—</span>}
        </span>
      </div>
      <ClausulaExpand texto={clausula} />
    </div>
  );
}

function SindicatoCard({ s, onAtualizar }) {
  const dataBase =
    s.database_mes
      ? `${MESES[s.database_mes] || s.database_mes}${s.database_ano ? ' / ' + s.database_ano : ''}`
      : null;

  const piso = s.piso_salarial
    ? `R$ ${Number(s.piso_salarial).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`
    : null;

  const dt = s.ultima_atualizacao
    ? new Date(s.ultima_atualizacao).toLocaleDateString('pt-BR')
    : null;

  return (
    <div className="bg-black/40 border border-white/5 rounded-[var(--v-radius)] hover:border-[#ff4d00]/20 transition-all duration-300 p-5 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[10px] font-black text-[var(--v-accent)] uppercase tracking-widest mb-1">
            {s.sigla || `SIND-${s.codigosind}`}
          </p>
          <h3 className="text-sm font-black text-[var(--v-text-bold)] leading-tight">
            {s.nome || `Sindicato ${s.codigosind}`}
          </h3>
          {s.cnpj && s.cnpj !== '00.000.000/0000-00' && (
            <p className="text-[9px] text-[var(--v-text-faint)] mt-1 font-mono">{s.cnpj}</p>
          )}
        </div>
        {s.url_pdf && (
          <a
            href={s.url_pdf}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 p-1.5 bg-white/5 border border-white/10 rounded-[var(--v-radius)] hover:border-[#ff4d00]/40 hover:bg-[var(--v-accent)]/10 transition-all"
            title="Abrir CCT (PDF)"
          >
            <ExternalLink size={12} className="text-[var(--v-text-muted)]" />
          </a>
        )}
      </div>

      {/* Dados */}
      <div className="bg-black/20 rounded-[var(--v-radius)] px-3 py-1">
        <InfoRow label="Piso Salarial" valor={piso} />
        <InfoRow label="Data Base" valor={dataBase} />
        <InfoRow
          label="Alimentação"
          valor={s.alimentacao_valor}
          clausula={s.alimentacao_clausula}
        />
        <InfoRow
          label="Transporte"
          valor={s.transporte_valor}
          clausula={s.transporte_clausula}
        />
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-auto pt-1">
        <StatusBadge status={s.status} />
        <div className="flex items-center gap-2">
          {dt && <span className="text-[9px] text-[var(--v-text-faint)]">{dt}</span>}
          <button
            onClick={() => onAtualizar()}
            className="p-1.5 bg-white/5 border border-white/5 rounded-[var(--v-radius)] hover:border-[#ff4d00]/40 hover:text-[var(--v-accent)] text-[var(--v-text-faint)] transition-all"
            title="Forçar atualização"
          >
            <RefreshCw size={11} />
          </button>
        </div>
      </div>

      {/* Erro inline */}
      {s.erro_msg && (
        <p className="text-[9px] text-[var(--v-accent)]/60 border border-[#ff4d00]/10 bg-[var(--v-accent)]/5 px-2 py-1 rounded-[var(--v-radius)] leading-relaxed">
          {s.erro_msg}
        </p>
      )}
    </div>
  );
}

export function SindicatosView() {
  const [sindicatos, setSindicatos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [atualizando, setAtualizando] = useState(false);
  const [erro, setErro] = useState(null);

  const carregar = useCallback(async () => {
    setErro(null);
    try {
      const resp = await fetch(`${API_BASE}/api/sindicatos`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setSindicatos(Array.isArray(data) ? data : []);
    } catch (e) {
      setErro(`Erro ao carregar sindicatos: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregar();
    // Polling a cada 15s enquanto houver registros pendentes
    const interval = setInterval(() => {
      setSindicatos((prev) => {
        const temPendente = prev.some((s) => s.status === 'pendente');
        if (temPendente) carregar();
        return prev;
      });
    }, 15000);
    return () => clearInterval(interval);
  }, [carregar]);

  const handleAtualizar = async () => {
    setAtualizando(true);
    try {
      await fetch(`${API_BASE}/api/sindicatos/atualizar`, { method: 'POST' });
      // Aguarda 2s e recarrega para mostrar status 'pendente'
      setTimeout(carregar, 2000);
    } catch (e) {
      setErro(`Erro ao disparar atualização: ${e.message}`);
    } finally {
      setTimeout(() => setAtualizando(false), 3000);
    }
  };

  const pendentes = sindicatos.filter((s) => s.status === 'pendente').length;
  const comErro = sindicatos.filter(
    (s) => s.status === 'erro' || s.status === 'pdf_nao_encontrado'
  ).length;
  const ok = sindicatos.filter((s) => s.status === 'ok').length;

  return (
    <div className="animate-in fade-in duration-500 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-headline text-2xl font-black tracking-tighter text-[var(--v-text-bold)] uppercase">
            Sindicatos — CCT
          </h2>
          <p className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest mt-1">
            Convenções Coletivas via MTE Mediador · Extração Gemini · Atualização diária
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Contadores */}
          <div className="flex gap-2 text-[9px] font-black uppercase tracking-widest">
            {ok > 0 && (
              <span className="px-2 py-1 bg-[#34c759]/10 border border-[#34c759]/20 text-[var(--v-accent-3)] rounded-[var(--v-radius)]">
                {ok} ok
              </span>
            )}
            {pendentes > 0 && (
              <span className="px-2 py-1 bg-[#ffcc00]/10 border border-[#ffcc00]/20 text-[var(--v-accent-6)] rounded-[var(--v-radius)]">
                {pendentes} buscando
              </span>
            )}
            {comErro > 0 && (
              <span className="px-2 py-1 bg-[var(--v-accent)]/10 border border-[#ff4d00]/20 text-[var(--v-accent)] rounded-[var(--v-radius)]">
                {comErro} sem CCT
              </span>
            )}
          </div>
          <button
            onClick={handleAtualizar}
            disabled={atualizando}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--v-accent)] text-black text-[9px] font-black uppercase tracking-widest rounded-[var(--v-radius)] hover:bg-white transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(255,77,0,0.3)]"
          >
            <RefreshCw size={12} className={atualizando ? 'animate-spin' : ''} />
            {atualizando ? 'Atualizando...' : 'Atualizar CCTs'}
          </button>
        </div>
      </div>

      {/* Erro global */}
      {erro && (
        <div className="border border-[#ff4d00]/30 bg-[var(--v-accent)]/5 text-[var(--v-accent)] text-xs font-bold px-4 py-3 rounded-[var(--v-radius)] flex items-center gap-2">
          <AlertTriangle size={14} />
          {erro}
        </div>
      )}

      {/* Loading inicial */}
      {loading && (
        <div className="flex justify-center py-24">
          <div className="flex flex-col items-center gap-4">
            <RefreshCw className="animate-spin text-[var(--v-accent)]" size={28} />
            <span className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-black">
              Carregando sindicatos...
            </span>
          </div>
        </div>
      )}

      {/* Grid de cards */}
      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
          {sindicatos.map((s) => (
            <SindicatoCard
              key={s.codigosind}
              s={s}
              onAtualizar={handleAtualizar}
            />
          ))}
          {sindicatos.length === 0 && (
            <div className="col-span-full text-center py-20 text-[var(--v-text-faint)] uppercase tracking-widest text-xs border border-white/5 rounded-[var(--v-radius)]">
              Nenhum sindicato carregado ainda.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
