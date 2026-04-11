import React, { useState, useEffect, useMemo } from 'react';
import { ShieldCheck, ChevronDown, ChevronUp, DollarSign, Filter, Search, Zap, AlertTriangle, Building } from 'lucide-react';

const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0);
const API_BASE = "http://127.0.0.1:8000";

const getCategoryForAccount = (nomeConta = '', codigoConta = '') => {
  const n = nomeConta.toLowerCase();
  const c = String(codigoConta);

  if (n.includes('tributo') || n.includes('imposto') || n.includes('csll') || n.includes('irpj') || n.includes('pis') || n.includes('cofins')) {
    if (n.includes('ret') || n.includes('socie')) return 'Tributos Societários';
    return 'Fiscais';
  }
  if (n.includes('cliente') || n.includes('adiantamento') || c.startsWith('1.02') || c.startsWith('1.03')) return 'Clientes e Adiantamentos';
  if (n.includes('custo') || n.includes('obra') || n.includes('poc') || c.startsWith('4')) return 'Custos (POC) & Obras';
  if (n.includes('receita') || n.includes('venda') || c.startsWith('3')) return 'Receita Societária';
  if (n.includes('caixa') || n.includes('banco') || c.startsWith('1.01')) return 'Caixa e Bancos';
  if (n.includes('fornecedor') || c.startsWith('2.01')) return 'Fornecedores';
  
  return 'Outras Operações';
};

const getCategoryColor = (cat) => {
  const map = {
    'Tributos Societários': '#ff4d00',
    'Fiscais': '#ffcc00',
    'Clientes e Adiantamentos': '#a259ff',
    'Custos (POC) & Obras': '#ff4d00',
    'Receita Societária': '#34c759',
    'Caixa e Bancos': '#34c759',
    'Outras Operações': '#888888'
  };
  return map[cat] || '#555';
};

export const NovoContabilizacoesView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [filtroEmpreendimento, setFiltroEmpreendimento] = useState('');
  const [expandedCards, setExpandedCards] = useState({});

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    let url = `${API_BASE}/api/vulcano/contabilizacoes?empresa_id=${selectedEmpresa}`;
    fetch(url)
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

  const uniqueEmpreendimentos = useMemo(() => {
    return [...new Set(data.map(d => d.centro_custo || 'Livro Físico (Padrão)'))].sort();
  }, [data]);

  const categoriesMap = useMemo(() => {
    const map = {};

    data.forEach(item => {
      let val = item.valor || 0;
      if (String(item.conta).includes('4845') && val < 0) {
        val = Math.abs(val);
      }

      const cc = item.centro_custo || 'Livro Físico (Padrão)';
      const nomeConta = item.nome_conta || '';
      const codigoConta = item.conta || '';
      const cat = getCategoryForAccount(nomeConta, codigoConta);
      const dataLancamento = item.data || '';
      const mesLancamento = dataLancamento ? dataLancamento.substring(0, 7) : 'Sem Data';

      if (filtroEmpreendimento && cc !== filtroEmpreendimento) return;
      
      const isBeforePeriod = dateFrom && dataLancamento < dateFrom;
      const isAfterPeriod = dateTo && dataLancamento > dateTo;
      const isWithinPeriod = !isBeforePeriod && !isAfterPeriod;

      if (!map[cat]) {
        map[cat] = {
          nome: cat,
          saldoAnterior: 0,
          movimentoPeriodo: 0,
          novoSaldo: 0,
          contas: {},
          mesesSet: new Set()
        };
      }

      const catRef = map[cat];
      
      if (isBeforePeriod) {
        catRef.saldoAnterior += val;
      }
      if (isWithinPeriod) {
        catRef.movimentoPeriodo += val;
        if (!catRef.contas[codigoConta]) {
          catRef.contas[codigoConta] = { nome: nomeConta, porMes: {}, total: 0 };
        }
        if (!catRef.contas[codigoConta].porMes[mesLancamento]) {
          catRef.contas[codigoConta].porMes[mesLancamento] = 0;
        }
        catRef.contas[codigoConta].porMes[mesLancamento] += val;
        catRef.contas[codigoConta].total += val;
        catRef.mesesSet.add(mesLancamento);
      }
      
      if (!isAfterPeriod) {
        catRef.novoSaldo += val;
      }
    });

    Object.keys(map).forEach(k => {
      if (map[k].contas && Object.keys(map[k].contas).length === 0 && map[k].saldoAnterior === 0 && map[k].novoSaldo === 0) {
        delete map[k];
      }
    });

    return map;
  }, [data, dateFrom, dateTo, filtroEmpreendimento]);

  const toggleCard = (cat) => {
    setExpandedCards(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  return (
    <div className="space-y-6 animate-in fade-in max-w-[1600px] mx-auto w-full h-full flex flex-col pb-6 text-[var(--v-text)]">
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-[var(--v-border)] pb-4">
        <div>
          <h2 className="text-3xl font-black tracking-tighter text-[var(--v-text-bold)] flex items-center gap-3">
            <ShieldCheck className="text-[var(--v-accent)]" size={36} /> Central de Conferência
          </h2>
          <p className="text-xs text-[var(--v-text-muted)] font-bold uppercase tracking-[0.3em] mt-2">Visão Consolidada de Operações &amp; Tributos</p>
        </div>
        
        <div className="flex gap-4 mt-6 md:mt-0 items-end">
          <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded flex items-center p-1 focus-within:border-[#ff4d00] transition-colors">
            <Search size={14} className="text-[var(--v-text-faint)] mx-3" />
            <select
              value={filtroEmpreendimento}
              onChange={(e) => setFiltroEmpreendimento(e.target.value)}
              className="bg-transparent border-none outline-none text-[var(--v-text)] text-xs py-2 pr-4 font-bold uppercase tracking-widest placeholder-[#555] cursor-pointer"
            >
              <option value="">Buscar Empreendimento...</option>
              {uniqueEmpreendimentos.map(emp => (
                <option key={emp} value={emp}>{emp}</option>
              ))}
            </select>
          </div>
          
          <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-2">
            <div className="flex items-center gap-2">
              <span className="text-[9px] uppercase font-bold text-[var(--v-text-faint)] tracking-widest">Início</span>
              <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="bg-transparent border-none outline-none text-[var(--v-text)] text-[10px] font-mono" />
            </div>
          </div>
          <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-2">
            <div className="flex items-center gap-2">
              <span className="text-[9px] uppercase font-bold text-[var(--v-text-faint)] tracking-widest">Fim</span>
              <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="bg-transparent border-none outline-none text-[var(--v-text)] text-[10px] font-mono" />
            </div>
          </div>
          <button
            onClick={() => { setDateFrom(''); setDateTo(''); setFiltroEmpreendimento(''); }}
            className="bg-[var(--v-hover)] border border-[var(--v-border)] hover:border-[#ff4d00] hover:text-[var(--v-accent)] text-[var(--v-text-muted)] font-bold uppercase tracking-widest text-[9px] px-4 py-3 rounded transition-all"
          >
            Limpar Filtros
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex gap-3 justify-center items-center py-12">
          <Zap className="animate-spin text-[var(--v-accent)]" size={32} />
          <span className="text-xs uppercase font-bold text-[var(--v-text-muted)] tracking-[0.2em]">Sincronizando Data Warehouse...</span>
        </div>
      )}

      <div className="flex flex-col gap-6 flex-1 overflow-hidden">
        {Object.keys(categoriesMap).length === 0 && !loading && (
          <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-12 text-center text-[var(--v-text-faint)]">
            <AlertTriangle className="mx-auto text-[var(--v-accent-6)] mb-4 opacity-50" size={48} />
            <h3 className="font-bold uppercase tracking-widest mb-1 text-[var(--v-text-bold)]">Nenhum Registro Contábil Encontrado</h3>
            <p className="text-[10px] uppercase font-bold">Verifique o período de data selecionado para o Empreendimento.</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 shrink-0 overflow-y-auto no-scrollbar">
          {Object.entries(categoriesMap).map(([catName, catData]) => {
             const color = getCategoryColor(catName);
             return (
               <div key={catName} className="bg-[var(--v-card)] border border-[var(--v-border)] rounded-[var(--v-radius)] hover:border-[var(--v-border)] transition-colors flex flex-col shadow-xl">
                 <div className="p-4 border-b border-[var(--v-border)] flex justify-between items-center" style={{ borderTop: `3px solid ${color}` }}>
                   <div className="flex items-center gap-3">
                     <Building size={16} style={{ color }} />
                     <h3 className="text-xs font-black uppercase tracking-widest text-[var(--v-text-bold)]">{catName}</h3>
                   </div>
                 </div>

                 <div className="p-5 flex flex-col gap-4">
                   <div className="flex justify-between items-end border-b border-[#2a2a2a] pb-3">
                      <div>
                        <p className="text-[9px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-1">Saldo Anterior</p>
                        <h4 className="text-xl font-mono text-[var(--v-text-muted)]">{formatCurrency(catData.saldoAnterior)}</h4>
                      </div>
                      <div className="text-right">
                        <p className="text-[9px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-1">Movimento Período</p>
                        <h4 className={`text-sm font-mono ${catData.movimentoPeriodo > 0 ? 'text-[var(--v-accent-3)]' : catData.movimentoPeriodo < 0 ? 'text-[var(--v-accent)]' : 'text-[var(--v-text-muted)]'}`}>
                          {catData.movimentoPeriodo > 0 ? '+' : ''}{formatCurrency(catData.movimentoPeriodo)}
                        </h4>
                      </div>
                   </div>
                   
                   <div className="bg-[var(--v-deep)] p-4 rounded border border-[var(--v-border)]">
                      <p className="text-[10px] font-black uppercase tracking-widest text-[var(--v-accent)] mb-1">Novo Saldo Consolidado</p>
                      <h3 className="text-3xl font-black text-[var(--v-text-bold)] tracking-tight">{formatCurrency(catData.novoSaldo)}</h3>
                   </div>
                   
                   <button 
                     onClick={() => toggleCard(catName)}
                     className="w-full mt-2 bg-[var(--v-hover)] border border-[var(--v-border)] hover:border-[#555] py-2 text-[9px] font-black uppercase tracking-[0.2em] text-[var(--v-text-muted)] hover:text-[var(--v-text-bold)] transition-all flex justify-center items-center gap-2 rounded"
                   >
                     {expandedCards[catName] ? <>Fechar Analítico <ChevronUp size={12}/></> : <>Ver Linhas Analíticas <ChevronDown size={12}/></>}
                   </button>
                 </div>

                 {expandedCards[catName] && (
                   <div className="border-t border-[var(--v-border)] bg-[var(--v-deep)] overflow-x-auto custom-scrollbar animate-in slide-in-from-top-2">
                     <table className="w-full text-left text-xs border-collapse">
                       <thead>
                         <tr>
                           <th className="p-3 text-[9px] tracking-[0.2em] font-black uppercase text-[var(--v-text-muted)] border-b border-[var(--v-border)] bg-[var(--v-deep)] sticky left-0 z-10 w-64 min-w-[200px]">Conta Débito/Crédito</th>
                           {Array.from(catData.mesesSet).sort().map(mes => (
                             <th key={mes} className="p-3 text-[9px] tracking-[0.2em] font-black uppercase text-[var(--v-text-faint)] border-b border-[var(--v-border)] text-right min-w-[100px]">{mes}</th>
                           ))}
                           <th className="p-3 text-[9px] tracking-[0.2em] font-black uppercase text-[var(--v-text-bold)] border-b border-[var(--v-border)] text-right min-w-[120px]">Total Acumulado</th>
                         </tr>
                       </thead>
                       <tbody>
                         {Object.entries(catData.contas).map(([cod, cInfo]) => (
                           <tr key={cod} className="border-b border-[#1f1f1f] hover:bg-[#151515]">
                             <td className="p-3 sticky left-0 z-10 bg-[var(--v-deep)] w-64 font-mono text-[var(--v-text-muted)]" title={cInfo.nome}>
                               <span className="font-bold text-[var(--v-text)] block mb-1">{cod}</span>
                               <span className="text-[9px] uppercase tracking-wider text-[var(--v-text-faint)] block truncate max-w-[220px]">{cInfo.nome}</span>
                             </td>
                             {Array.from(catData.mesesSet).sort().map(mes => (
                               <td key={mes} className="p-3 text-right font-mono text-[var(--v-text-muted)]">
                                 {cInfo.porMes[mes] ? formatCurrency(cInfo.porMes[mes]) : <span className="text-[#333]">-</span>}
                               </td>
                             ))}
                             <td className="p-3 text-right font-mono font-bold text-[var(--v-accent)]">{formatCurrency(cInfo.total)}</td>
                           </tr>
                         ))}
                         {Object.keys(catData.contas).length === 0 && (
                            <tr><td colSpan="100%" className="p-4 text-center text-[var(--v-text-faint)] text-[10px] uppercase font-bold italic">Nenhum movimento analítico no período selecionado.</td></tr>
                         )}
                       </tbody>
                     </table>
                   </div>
                 )}
               </div>
             );
          })}
        </div>
      </div>
    </div>
  );
};
