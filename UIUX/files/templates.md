# Templates

Full, working templates to start from. Copy the structure, adapt the content. Do not deviate from the density rules.

## Table of contents

1. [Dashboard Mode — Conciliação + Racional inline](#dashboard-mode)
2. [Spreadsheet Mode — Lançamento em massa](#spreadsheet-mode)
3. [Field components](#field-components)
4. [Inline expand pattern (racional + histórico)](#inline-expand)

---

## Dashboard Mode

Use when: dashboards, conciliação, confronto, auditoria, visão geral com KPIs + tabela.

### Structure

```
┌─────────────────────────────────────────────────────────┐
│ Filter bar — 48px                                       │ ← filters debounce-apply
├─────────────────────────────────────────────────────────┤
│ KPI row — 64px  [4-6 metric cards]                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Main grid — fills remaining                             │
│ dense rows, inline expand for racional                  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ Status legend — 24px sticky bottom                      │
└─────────────────────────────────────────────────────────┘
```

### DashboardTemplate.jsx

```jsx
import { useState, useMemo } from 'react';
import './DashboardTemplate.css';

// Dummy data — replace with real source
const sampleRows = [
  { id: 1, conta: 'APTO 302', questor: -7476.25, sistema: -8797.73, status: 'DIVERGENTE' },
  { id: 2, conta: 'APTO 305', questor: -6083.50, sistema: -14317.61, status: 'DIVERGENTE' },
  { id: 3, conta: 'APTO 401', questor: -259780.30, sistema: -515121.05, status: 'DIVERGENTE' },
];

const brl = (n) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(n);

export default function DashboardTemplate() {
  const [period, setPeriod] = useState({ from: '2025-04', to: '2025-04' });
  const [entity, setEntity] = useState('todos');
  const [onlyWithMovement, setOnlyWithMovement] = useState(false);
  const [expandedRow, setExpandedRow] = useState(null);

  const kpis = useMemo(() => {
    const totalQuestor = sampleRows.reduce((a, r) => a + r.questor, 0);
    const totalSistema = sampleRows.reduce((a, r) => a + r.sistema, 0);
    const diff = totalSistema - totalQuestor;
    const ok = sampleRows.filter((r) => r.status === 'OK').length;
    const div = sampleRows.filter((r) => r.status === 'DIVERGENTE').length;
    const aderencia = (ok / (ok + div || 1)) * 100;
    return { totalQuestor, totalSistema, diff, ok, div, aderencia };
  }, []);

  return (
    <div className="dash">
      {/* Filter bar */}
      <div className="dash__filters">
        <label className="field">
          <span>Período de</span>
          <input
            type="month"
            value={period.from}
            onChange={(e) => setPeriod({ ...period, from: e.target.value })}
          />
        </label>
        <label className="field">
          <span>Até</span>
          <input
            type="month"
            value={period.to}
            onChange={(e) => setPeriod({ ...period, to: e.target.value })}
          />
        </label>
        <label className="field field--grow">
          <span>Empreendimento</span>
          <select value={entity} onChange={(e) => setEntity(e.target.value)}>
            <option value="todos">Todos os empreendimentos</option>
          </select>
        </label>
        <button
          className={`toggle ${onlyWithMovement ? 'toggle--on' : ''}`}
          onClick={() => setOnlyWithMovement((v) => !v)}
        >
          Somente c/ movimento
        </button>
        <button className="btn btn--primary">Auditar</button>
      </div>

      {/* KPI row */}
      <div className="dash__kpis">
        <Kpi
          label="Conciliação Global"
          value={`${kpis.aderencia.toFixed(0)}%`}
          sub={`${kpis.ok} OK · ${kpis.div} div.`}
          bar={kpis.aderencia}
        />
        <Kpi label="Movimento total Questor" value={brl(kpis.totalQuestor)} />
        <Kpi label="Movimento total sistema" value={brl(kpis.totalSistema)} />
        <Kpi
          label="Diferença"
          value={brl(kpis.diff)}
          tone={kpis.diff !== 0 ? 'divergent' : 'ok'}
        />
      </div>

      {/* Main grid */}
      <div className="dash__grid">
        <div className="grid__head">
          <div>Conta</div>
          <div className="num">Questor</div>
          <div className="num">Sistema</div>
          <div className="num">Diferença</div>
          <div>Status</div>
          <div></div>
        </div>
        {sampleRows.map((r) => {
          const diff = r.sistema - r.questor;
          const expanded = expandedRow === r.id;
          return (
            <div key={r.id} className={`grid__row ${expanded ? 'grid__row--open' : ''}`}>
              <div className="grid__cells">
                <div>{r.conta}</div>
                <div className="num">{brl(r.questor)}</div>
                <div className="num">{brl(r.sistema)}</div>
                <div className="num neg">{brl(diff)}</div>
                <div>
                  <span className={`status status--${r.status.toLowerCase()}`}>
                    ● {r.status}
                  </span>
                </div>
                <div className="grid__actions">
                  <button
                    className="affordance"
                    title="Ver racional"
                    onClick={() => setExpandedRow(expanded ? null : r.id)}
                  >
                    ƒ
                  </button>
                  <button className="affordance" title="Histórico">⟳</button>
                </div>
              </div>
              {expanded && (
                <div className="grid__expand">
                  <div className="racional">
                    <div className="racional__title">Racional — {r.conta}</div>
                    <table className="racional__table">
                      <tbody>
                        <tr>
                          <td>Saldo inicial</td>
                          <td className="num">{brl(0)}</td>
                        </tr>
                        <tr>
                          <td>(+) Movimentos crédito</td>
                          <td className="num">{brl(Math.abs(r.sistema) * 0.3)}</td>
                        </tr>
                        <tr>
                          <td>(−) Movimentos débito</td>
                          <td className="num neg">{brl(Math.abs(r.sistema))}</td>
                        </tr>
                        <tr className="racional__total">
                          <td>Saldo sistema</td>
                          <td className="num">{brl(r.sistema)}</td>
                        </tr>
                        <tr className="racional__total">
                          <td>Saldo Questor</td>
                          <td className="num">{brl(r.questor)}</td>
                        </tr>
                        <tr className="racional__diff">
                          <td>Divergência</td>
                          <td className="num neg">{brl(diff)}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Status legend */}
      <div className="dash__legend">
        <span><span className="status status--ok">●</span> OK</span>
        <span><span className="status status--divergente">●</span> Divergente</span>
        <span><span className="status status--warn">●</span> Parcial</span>
        <span className="legend__shortcuts">
          <kbd>ƒ</kbd> racional · <kbd>⟳</kbd> histórico · <kbd>/</kbd> buscar
        </span>
      </div>
    </div>
  );
}

function Kpi({ label, value, sub, bar, tone }) {
  return (
    <div className={`kpi ${tone ? `kpi--${tone}` : ''}`}>
      <div className="kpi__label">{label}</div>
      <div className="kpi__value">{value}</div>
      {sub && <div className="kpi__sub">{sub}</div>}
      {bar !== undefined && (
        <div className="kpi__bar">
          <div className="kpi__bar-fill" style={{ width: `${bar}%` }} />
        </div>
      )}
    </div>
  );
}
```

### DashboardTemplate.css

```css
.dash {
  display: grid;
  grid-template-rows: 48px 64px 1fr 24px;
  height: 100vh;
  background: var(--bg-app);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: var(--fs-base);
}

/* --- Filter bar --- */
.dash__filters {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 0 var(--sp-3);
  border-bottom: 1px solid var(--border);
  background: var(--bg-panel);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.field--grow { flex: 1; max-width: 320px; }
.field > span {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
.field input,
.field select {
  height: 28px;
  background: var(--bg-cell);
  border: 1px solid var(--border);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: var(--fs-sm);
  padding: 0 var(--sp-2);
  border-radius: var(--r-md);
}
.field input:focus,
.field select:focus {
  outline: none;
  border-color: var(--border-focus);
}

.toggle {
  height: 28px;
  padding: 0 var(--sp-3);
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-size: var(--fs-sm);
  cursor: pointer;
  border-radius: var(--r-md);
}
.toggle--on {
  background: rgba(255, 107, 26, 0.08);
  border-color: var(--action);
  color: var(--action);
}

.btn {
  height: 28px;
  padding: 0 var(--sp-4);
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text);
  font-size: var(--fs-sm);
  cursor: pointer;
  border-radius: var(--r-md);
}
.btn--primary {
  background: var(--action);
  border-color: var(--action);
  color: #000;
  font-weight: 600;
}
.btn--primary:hover { background: var(--action-hover); }

/* --- KPI row --- */
.dash__kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1px;
  background: var(--border);
  border-bottom: 1px solid var(--border);
}
.kpi {
  padding: var(--sp-2) var(--sp-3);
  background: var(--bg-panel);
}
.kpi__label {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.kpi__value {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: var(--fs-xl);
  font-weight: 600;
  margin-top: 2px;
}
.kpi__sub {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  margin-top: 2px;
}
.kpi__bar {
  height: 3px;
  background: var(--border);
  margin-top: var(--sp-1);
}
.kpi__bar-fill {
  height: 100%;
  background: var(--status-warn);
  transition: width var(--t-base);
}
.kpi--divergent .kpi__value { color: var(--status-divergent); }
.kpi--ok .kpi__value { color: var(--status-ok); }

/* --- Grid --- */
.dash__grid {
  overflow-y: auto;
  overflow-x: hidden;
}
.grid__head,
.grid__cells {
  display: grid;
  grid-template-columns: 1fr 140px 140px 140px 120px 80px;
  align-items: center;
  padding: 0 var(--sp-3);
  height: 32px;
  border-bottom: 1px solid var(--border);
}
.grid__head {
  position: sticky;
  top: 0;
  background: var(--bg-panel);
  color: var(--text-muted);
  font-size: var(--fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  z-index: 2;
}
.grid__row {
  background: var(--bg-app);
}
.grid__row:hover { background: var(--bg-panel-hover); }
.grid__row--open { background: var(--bg-panel); }

.num {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  text-align: right;
}
.neg { color: var(--status-error); }

.status {
  font-size: var(--fs-xs);
  letter-spacing: 0.02em;
}
.status--ok { color: var(--status-ok); }
.status--divergente { color: var(--status-divergent); }
.status--warn { color: var(--status-warn); }

.grid__actions { display: flex; gap: var(--sp-1); justify-content: flex-end; }
.affordance {
  width: 22px; height: 22px;
  display: inline-flex; align-items: center; justify-content: center;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
  cursor: pointer;
  border-radius: var(--r-sm);
}
.affordance:hover {
  border-color: var(--action);
  color: var(--action);
}

/* --- Inline expand (racional) --- */
.grid__expand {
  border-bottom: 1px solid var(--border);
  background: var(--bg-panel);
  padding: var(--sp-3);
}
.racional__title {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--sp-2);
}
.racional__table {
  width: 100%;
  max-width: 520px;
  border-collapse: collapse;
}
.racional__table td {
  padding: 4px var(--sp-2);
  border-bottom: 1px solid var(--border);
  font-size: var(--fs-sm);
}
.racional__table td:last-child {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  text-align: right;
  min-width: 140px;
}
.racional__total td {
  border-top: 1px solid var(--border-strong);
  font-weight: 600;
}
.racional__diff td { color: var(--status-divergent); font-weight: 600; }

/* --- Legend --- */
.dash__legend {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: 0 var(--sp-3);
  font-size: var(--fs-xs);
  color: var(--text-muted);
  background: var(--bg-panel);
  border-top: 1px solid var(--border);
}
.legend__shortcuts { margin-left: auto; }
kbd {
  display: inline-block;
  padding: 0 4px;
  font-family: var(--font-mono);
  font-size: 10px;
  background: var(--bg-cell);
  border: 1px solid var(--border);
  border-radius: 2px;
}
```

---

## Spreadsheet Mode

Use when: "tela de lançamento", entrada de dados em massa, registros em volume.

### SpreadsheetTemplate.jsx

```jsx
import { useState, useRef, useCallback } from 'react';
import './SpreadsheetTemplate.css';

const columns = [
  { key: 'data', label: 'Data', width: 110, type: 'date' },
  { key: 'conta', label: 'Conta', width: 120, type: 'text' },
  { key: 'historico', label: 'Histórico', width: 280, type: 'text' },
  { key: 'debito', label: 'Débito', width: 130, type: 'number' },
  { key: 'credito', label: 'Crédito', width: 130, type: 'number' },
];

const emptyRow = () => ({
  id: crypto.randomUUID(),
  data: '', conta: '', historico: '', debito: '', credito: '',
  errors: {},
});

const brlInput = (v) => {
  if (v === '' || v === null || v === undefined) return '';
  return Number(v).toLocaleString('pt-BR', {
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  });
};
const parseBrl = (s) => {
  if (!s) return '';
  const n = Number(String(s).replace(/\./g, '').replace(',', '.'));
  return isNaN(n) ? '' : n;
};

export default function SpreadsheetTemplate() {
  const [rows, setRows] = useState(() => Array.from({ length: 5 }, emptyRow));
  const [dirty, setDirty] = useState(0);
  const refs = useRef({});

  const focusCell = (rowIdx, colIdx) => {
    const row = rows[rowIdx];
    if (!row) return;
    const col = columns[colIdx];
    if (!col) return;
    refs.current[`${row.id}-${col.key}`]?.focus();
  };

  const handleKeyDown = useCallback(
    (e, rowIdx, colIdx) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const dir = e.shiftKey ? -1 : 1;
        focusCell(rowIdx, colIdx + dir);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (rowIdx === rows.length - 1 && !e.shiftKey) {
          setRows((rs) => [...rs, emptyRow()]);
          setTimeout(() => focusCell(rowIdx + 1, colIdx), 0);
        } else {
          focusCell(rowIdx + (e.shiftKey ? -1 : 1), colIdx);
        }
      } else if (e.key === 'ArrowDown' && e.ctrlKey === false) {
        e.preventDefault();
        focusCell(rowIdx + 1, colIdx);
      } else if (e.key === 'ArrowUp' && e.ctrlKey === false) {
        e.preventDefault();
        focusCell(rowIdx - 1, colIdx);
      } else if (e.key === 'd' && e.ctrlKey) {
        e.preventDefault();
        if (rowIdx > 0) {
          const above = rows[rowIdx - 1];
          setRows((rs) =>
            rs.map((r, i) =>
              i === rowIdx ? { ...above, id: r.id, errors: {} } : r
            )
          );
          setDirty((d) => d + 1);
        }
      }
    },
    [rows]
  );

  const updateCell = (rowIdx, key, value) => {
    setRows((rs) =>
      rs.map((r, i) => (i === rowIdx ? { ...r, [key]: value } : r))
    );
    setDirty((d) => d + 1);
  };

  const validateCell = (rowIdx, key, value) => {
    let err = '';
    if (key === 'debito' || key === 'credito') {
      if (value !== '' && isNaN(Number(value))) err = 'Valor inválido';
    }
    if (key === 'conta' && value && !/^\d+$/.test(value)) err = 'Apenas números';
    setRows((rs) =>
      rs.map((r, i) =>
        i === rowIdx
          ? { ...r, errors: { ...r.errors, [key]: err || undefined } }
          : r
      )
    );
  };

  const duplicateRow = (rowIdx) => {
    setRows((rs) => {
      const copy = [...rs];
      copy.splice(rowIdx + 1, 0, { ...rs[rowIdx], id: crypto.randomUUID(), errors: {} });
      return copy;
    });
    setDirty((d) => d + 1);
  };
  const deleteRow = (rowIdx) => {
    setRows((rs) => rs.filter((_, i) => i !== rowIdx));
    setDirty((d) => d + 1);
  };

  const totals = columns
    .filter((c) => c.type === 'number')
    .reduce((acc, c) => {
      acc[c.key] = rows.reduce((s, r) => s + (Number(parseBrl(r[c.key])) || 0), 0);
      return acc;
    }, {});

  return (
    <div className="sheet">
      <div className="sheet__head">
        <div className="sheet__title">Lançamentos contábeis</div>
        <div className="sheet__status">
          {dirty > 0 ? (
            <span className="sheet__dirty">{dirty} alterações não salvas</span>
          ) : (
            <span className="sheet__clean">Salvo</span>
          )}
          <button className="btn btn--primary" disabled={dirty === 0}>
            Salvar tudo
          </button>
        </div>
      </div>

      <div className="sheet__grid">
        <div
          className="sheet__row sheet__row--head"
          style={{
            gridTemplateColumns: `44px ${columns.map((c) => `${c.width}px`).join(' ')} 1fr`,
          }}
        >
          <div className="sheet__cell sheet__cell--num">#</div>
          {columns.map((c) => (
            <div
              key={c.key}
              className={`sheet__cell ${c.type === 'number' ? 'sheet__cell--right' : ''}`}
            >
              {c.label}
            </div>
          ))}
          <div className="sheet__cell"></div>
        </div>

        {rows.map((row, rowIdx) => (
          <div
            key={row.id}
            className="sheet__row"
            style={{
              gridTemplateColumns: `44px ${columns.map((c) => `${c.width}px`).join(' ')} 1fr`,
            }}
          >
            <div className="sheet__cell sheet__cell--num sheet__cell--sticky">
              {rowIdx + 1}
              <span className="sheet__row-actions">
                <button
                  className="affordance"
                  title="Duplicar linha"
                  onClick={() => duplicateRow(rowIdx)}
                >
                  ⎘
                </button>
                <button
                  className="affordance affordance--danger"
                  title="Excluir linha"
                  onClick={() => deleteRow(rowIdx)}
                >
                  ×
                </button>
              </span>
            </div>
            {columns.map((c, colIdx) => {
              const hasError = !!row.errors[c.key];
              return (
                <div
                  key={c.key}
                  className={`sheet__cell sheet__cell--input ${
                    hasError ? 'sheet__cell--error' : ''
                  } ${c.type === 'number' ? 'sheet__cell--right' : ''}`}
                  title={row.errors[c.key] || ''}
                >
                  <input
                    ref={(el) => (refs.current[`${row.id}-${c.key}`] = el)}
                    type={c.type === 'date' ? 'date' : 'text'}
                    inputMode={c.type === 'number' ? 'decimal' : undefined}
                    value={row[c.key]}
                    onChange={(e) => updateCell(rowIdx, c.key, e.target.value)}
                    onBlur={(e) => validateCell(rowIdx, c.key, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(e, rowIdx, colIdx)}
                  />
                </div>
              );
            })}
            <div className="sheet__cell"></div>
          </div>
        ))}

        {/* Totals */}
        <div
          className="sheet__row sheet__row--totals"
          style={{
            gridTemplateColumns: `44px ${columns.map((c) => `${c.width}px`).join(' ')} 1fr`,
          }}
        >
          <div className="sheet__cell sheet__cell--num">Σ</div>
          {columns.map((c) => (
            <div
              key={c.key}
              className={`sheet__cell ${c.type === 'number' ? 'sheet__cell--right num' : ''}`}
            >
              {c.type === 'number' ? brlInput(totals[c.key]) : ''}
            </div>
          ))}
          <div className="sheet__cell">
            <span className="sheet__count">{rows.length} linhas</span>
          </div>
        </div>
      </div>

      <div className="sheet__foot">
        <button
          className="btn"
          onClick={() => setRows((rs) => [...rs, emptyRow()])}
        >
          + Adicionar linha
        </button>
        <span className="sheet__shortcuts">
          <kbd>Tab</kbd>/<kbd>Shift+Tab</kbd> navegar ·{' '}
          <kbd>Enter</kbd> nova linha · <kbd>Ctrl+D</kbd> preencher acima
        </span>
      </div>
    </div>
  );
}
```

### SpreadsheetTemplate.css

```css
.sheet {
  display: grid;
  grid-template-rows: 40px 1fr 32px;
  height: 100vh;
  background: var(--bg-app);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: var(--fs-base);
}

.sheet__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--sp-3);
  border-bottom: 1px solid var(--border);
  background: var(--bg-panel);
}
.sheet__title {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.sheet__status { display: flex; align-items: center; gap: var(--sp-3); }
.sheet__dirty { color: var(--status-warn); font-size: var(--fs-sm); }
.sheet__clean { color: var(--status-ok); font-size: var(--fs-sm); }

.sheet__grid {
  overflow: auto;
}

.sheet__row {
  display: grid;
  height: 28px;
  border-bottom: 1px solid var(--border);
}
.sheet__row--head {
  position: sticky;
  top: 0;
  background: var(--bg-panel);
  color: var(--text-muted);
  font-size: var(--fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  z-index: 3;
  height: 26px;
}
.sheet__row--totals {
  position: sticky;
  bottom: 0;
  background: var(--bg-panel);
  border-top: 1px solid var(--border-strong);
  font-weight: 600;
  z-index: 2;
}

.sheet__cell {
  display: flex;
  align-items: center;
  padding: 0 var(--sp-2);
  border-right: 1px solid var(--border);
  overflow: hidden;
  white-space: nowrap;
}
.sheet__cell--right { justify-content: flex-end; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.sheet__cell--num {
  background: var(--bg-panel);
  color: var(--text-muted);
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
}
.sheet__cell--sticky { position: sticky; left: 0; z-index: 1; }
.sheet__cell--input { padding: 0; }
.sheet__cell--input input {
  width: 100%;
  height: 100%;
  padding: 0 var(--sp-2);
  background: transparent;
  border: 0;
  color: var(--text);
  font: inherit;
}
.sheet__cell--right input { text-align: right; font-family: var(--font-mono); }
.sheet__cell--input input:focus {
  outline: none;
  background: var(--bg-cell-edit);
  box-shadow: inset 0 0 0 1px var(--border-focus);
}
.sheet__cell--error {
  box-shadow: inset 2px 0 0 var(--status-error);
}

.sheet__row-actions {
  display: none;
  gap: 2px;
}
.sheet__row:hover .sheet__row-actions { display: inline-flex; }

.affordance--danger:hover {
  border-color: var(--status-error);
  color: var(--status-error);
}

.sheet__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--sp-3);
  border-top: 1px solid var(--border);
  background: var(--bg-panel);
  font-size: var(--fs-xs);
  color: var(--text-muted);
}
.sheet__shortcuts kbd {
  margin: 0 2px;
}
```

---

## Field components

### Input de valor BR

```jsx
export function CurrencyInput({ value, onChange, ...rest }) {
  const format = (v) =>
    v === '' || v === null || v === undefined
      ? ''
      : Number(v).toLocaleString('pt-BR', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });

  const parse = (s) => {
    if (!s) return '';
    const n = Number(String(s).replace(/\./g, '').replace(',', '.'));
    return isNaN(n) ? '' : n;
  };

  return (
    <input
      inputMode="decimal"
      value={format(value)}
      onChange={(e) => onChange(parse(e.target.value))}
      {...rest}
    />
  );
}
```

### Status pill

```jsx
export function Status({ kind, label }) {
  return <span className={`status status--${kind}`}>● {label}</span>;
}
```

---

## Inline expand

Always the same pattern: a row, an affordance button (`ƒ` for racional, `⟳` for histórico), and an expanded block below the row — not a modal, not a drawer. The expanded block lives in the natural flow of the grid so scroll position is preserved.

Rules:
- The affordance is 22×22px, sits at the end of the row.
- When expanded, the row above gets `background: var(--bg-panel)` to visually anchor.
- `Esc` closes the expanded row.
- Only one row can be expanded at a time by default — if the user wants multi-expand, they must ask for it explicitly.
