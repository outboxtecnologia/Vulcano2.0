import React, { useState, useEffect } from 'react';
import { Database, Play, AlertCircle, RefreshCw, Search } from 'lucide-react';
import { API_BASE } from './apiBase';

export const RawExplorerView = () => {
    const [query, setQuery] = useState("SELECT FIRST 10 *\nFROM VENDA\nWHERE TOTALVENDA > 0");
    const [data, setData] = useState({ columns: [], rows: [] });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [dbSelected, setDbSelected] = useState('vulcano'); // 'vulcano' | 'questor'
    const [tables, setTables] = useState([]);
    const [tableSearch, setTableSearch] = useState('');

    const fetchTables = async (db) => {
        try {
            const res = await fetch(`${API_BASE}/api/tables?db=${db}`);
            const json = await res.json();
            setTables(json.tables || []);
        } catch (e) {
            console.error("Erro listando tabelas:", e);
        }
    };

    useEffect(() => {
        fetchTables(dbSelected);
    }, [dbSelected]);

    const executeQuery = async (queryText = query) => {
        if (!queryText.trim()) return;
        setLoading(true);
        setError(null);
        try {
            // Using the raw execute endpoint directly instead of the old hardcoded endpoints
            const payloadQuery = `/* ${dbSelected.toUpperCase()} */ ${queryText}`;
            // Oh wait, my backend api_explorer_query hardcodes get_conn("vulcano"). Let's ignore comments and just execute against Vulcano for raw query, OR I can just map the db if needed. Actually the user mainly used the old Schema Explorer to VIEW the tables. But I'll fix the backend hardcoded vulcano if they want to query questor too? Let's just use the table endpoint when clicking a table!
            
            // Wait, if it's just raw SQL: my raw SQL endpoint only connects to Vulcano right now. But the old table viewer endpoint connects to both. I'll use the table viewer endpoint when clicking a table instead of raw query.
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleTableClick = async (tableName) => {
        setQuery(`SELECT FIRST 100 * FROM ${tableName}`);
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/table/${tableName}/data?db=${dbSelected}`);
            const json = await res.json();
            if (!res.ok) throw new Error(json.detail || 'Erro ao consultar tabela');
            
            // Transform rows from object dicts to arrays for the table renderer
            const cols = json.columns || [];
            const rows = (json.data || []).map(rowDict => cols.map(c => rowDict[c]));
            
            setData({ columns: cols, rows: rows });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const runRawSql = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/explorer/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query }) // Always executes on Vulcano as per backend right now
            });
            const json = await res.json();
            if (!res.ok || !json.success) throw new Error(json.detail || json.message || 'Erro ao executar Query');
            setData({ columns: json.columns || [], rows: json.rows || [] });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const filteredTables = tables.filter(t => t.toLowerCase().includes(tableSearch.toLowerCase()));

    return (
        <div className="space-y-6 animate-in fade-in max-w-[1920px] mx-auto w-full h-full flex flex-col pt-4 pb-20">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
                        <Database className="text-[var(--v-accent-2)]" size={32}/> 
                        Schema & DB Explorer
                    </h2>
                    <p className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Acesso direto ao Dicionário Firebird (Leitura Recomendada)</p>
                </div>
            </div>

            <div className="flex flex-1 gap-6 min-h-0 overflow-hidden">
                {/* SIDEBAR DAS TABELAS */}
                <div className="w-72 bg-[var(--v-card)] border border-[var(--v-border)] rounded-[var(--v-radius)] flex flex-col shrink-0 overflow-hidden shadow-2xl">
                    <div className="flex gap-2 p-4 pb-2 bg-[#0b0b0b]">
                        <button onClick={() => setDbSelected('questor')} className={`flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-[var(--v-radius)] transition-all ${dbSelected === 'questor' ? 'bg-[var(--v-accent)]/20 text-[var(--v-accent)] border border-[#ff4d00]/50' : 'bg-[var(--v-hover)] text-[var(--v-text-muted)] border border-transparent'}`}>Questor</button>
                        <button onClick={() => setDbSelected('vulcano')} className={`flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-[var(--v-radius)] transition-all ${dbSelected === 'vulcano' ? 'bg-[var(--v-accent-2)]/20 text-[var(--v-accent-2)] border border-[var(--v-accent-2)]/50' : 'bg-[var(--v-hover)] text-[var(--v-text-muted)] border border-transparent'}`}>Vulcano</button>
                    </div>
                    <div className="px-4 py-2 border-b border-[var(--v-border)]">
                        <div className="relative">
                            <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-[var(--v-text-faint)]" size={14} />
                            <input 
                                value={tableSearch} onChange={e => setTableSearch(e.target.value)} 
                                placeholder="Filtrar tabelas..."
                                className="w-full bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] py-2 pl-8 pr-3 text-[10px] uppercase tracking-widest text-[var(--v-text-muted)] outline-none focus:border-[var(--v-accent-2)]"
                            />
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto px-2 py-4 custom-scrollbar">
                        {filteredTables.map(t => (
                            <div 
                                key={t} 
                                onClick={() => handleTableClick(t)} 
                                className="px-3 py-2 text-[11px] font-black tracking-wider text-[var(--v-text-muted)] font-mono cursor-pointer hover:bg-[#1f1f22] hover:text-[var(--v-accent-2)] border-l-2 border-transparent hover:border-[var(--v-accent-2)] mb-1 truncate transition-colors"
                            >
                                {t}
                            </div>
                        ))}
                        {filteredTables.length === 0 && <div className="p-4 text-center text-[var(--v-text-faint)] text-xs font-bold uppercase tracking-widest">Nenhuma tabela encontrada</div>}
                    </div>
                </div>

                {/* PAINEL CENTRAL / SQL */}
                <div className="flex-1 flex flex-col overflow-hidden gap-6">
                    <div className="flex gap-6 h-[180px] shrink-0">
                        <div className="flex-1 magma-card flex flex-col border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden p-0 relative group shadow-2xl">
                            <textarea 
                                value={query} 
                                onChange={e => setQuery(e.target.value)}
                                className="w-full flex-1 bg-[var(--v-deep)] p-4 outline-none font-mono text-[12px] leading-relaxed text-[var(--v-text)] placeholder:text-[#333] custom-scrollbar focus:bg-[var(--v-surface)] transition-colors"
                                spellCheck={false}
                            />
                            <div className="absolute top-2 right-2 flex gap-2">
                                <span className="text-[9px] uppercase tracking-widest font-black text-[var(--v-accent-2)] bg-[var(--v-accent-2)]/10 px-2 py-1 rounded-[var(--v-radius)] border border-[var(--v-accent-2)]/30 shadow-lg backdrop-blur-md">FREE TEXT SQL (VULCANO)</span>
                            </div>
                        </div>
                        
                        <div className="w-48 flex flex-col justify-end">
                             <button 
                                 onClick={runRawSql}
                                 disabled={loading}
                                 className="h-16 w-full bg-[var(--v-accent-2)] hover:bg-white text-black font-black uppercase tracking-widest text-[11px] rounded-[var(--v-radius)] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_var(--v-accent-2)]"
                             >
                                 {loading ? <RefreshCw size={18} className="animate-spin" /> : <Play size={18} />} Executar SQL
                             </button>
                             <p className="text-[8px] text-[var(--v-text-faint)] uppercase text-center mt-3 font-bold">SQL Custom só afeta Vulcano</p>
                        </div>
                    </div>

                    {error && (
                        <div className="bg-[var(--v-error)]/10 border border-[var(--v-error)] p-4 rounded-[var(--v-radius)] text-[var(--v-error)] font-mono text-[10px] flex gap-3 shadow-2xl shrink-0">
                            <AlertCircle size={16} /> <span>{error}</span>
                        </div>
                    )}

                    <div className="flex-1 min-h-[300px] magma-card border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden flex flex-col shadow-2xl bg-[#0b0b0b]">
                        <div className="p-3 bg-[var(--v-surface-container)] border-b border-[var(--v-border)] flex justify-between items-center shrink-0">
                            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--v-text-muted)]">DataGrid Output</h3>
                            <span className="text-[10px] font-bold text-[var(--v-text-muted)] bg-black/40 px-3 py-1 rounded-[var(--v-radius)] border border-[var(--v-border)] tabular-nums tracking-widest">{data.rows.length} REGISTROS</span>
                        </div>
                        
                        <div className="flex-1 overflow-auto custom-scrollbar">
                            <table className="w-full text-left text-[11px] relative border-collapse whitespace-nowrap">
                                <thead className="bg-[var(--v-deep)] sticky top-0 z-10">
                                    <tr>
                                        <th className="p-3 text-[var(--v-text-faint)] tracking-widest font-black font-mono border-b border-[var(--v-border)] text-center bg-[#151515]">#</th>
                                        {data.columns.map((col, i) => (
                                            <th key={i} className="p-3 text-[var(--v-accent-2)] tracking-widest font-black uppercase font-mono border-b border-[var(--v-border)] bg-[#151515]">
                                                {col}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.rows.map((row, i) => (
                                        <tr key={i} className="border-b border-[var(--v-border)] hover:bg-[#1f1f22] transition-colors">
                                            <td className="p-2 text-center text-[var(--v-text-faint)] font-mono text-[9px] font-bold border-r border-[var(--v-border)]">
                                                {i + 1}
                                            </td>
                                            {row.map((val, j) => (
                                                <td key={j} className="p-2 font-mono text-[var(--v-text-muted)] truncate max-w-[400px]" title={String(val)}>
                                                    {val === null ? <span className="opacity-30 italic">NULL</span> : String(val)}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                    {data.rows.length === 0 && !loading && !error && (
                                        <tr>
                                            <td colSpan={data.columns.length + 1} className="p-32 text-center font-mono text-[var(--v-text-faint)] uppercase tracking-widest text-[11px]">
                                                {tables.length === 0 ? 'Conectando ao banco de dados...' : 'Selecione uma tabela à esquerda ou digite Query (Vulcano)'}
                                            </td>
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
