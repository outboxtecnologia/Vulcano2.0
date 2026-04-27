# Brazilian formatting utilities

Copy-paste these into components that need them. Plain JS, no dependencies.

---

## Currency (R$)

```js
// Format: number → "R$ 1.234,56"
export const brl = (n, opts = {}) => {
  if (n === null || n === undefined || n === '') return '';
  const { withSymbol = true, fractionDigits = 2 } = opts;
  return new Intl.NumberFormat('pt-BR', {
    style: withSymbol ? 'currency' : 'decimal',
    currency: 'BRL',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(n);
};

// Parse: "1.234,56" or "R$ 1.234,56" → 1234.56
export const parseBrl = (s) => {
  if (s === null || s === undefined || s === '') return '';
  const cleaned = String(s).replace(/[R$\s]/g, '').replace(/\./g, '').replace(',', '.');
  const n = Number(cleaned);
  return isNaN(n) ? '' : n;
};

// Input mask: always formats as user types
export const brlMask = (raw) => {
  const digits = String(raw).replace(/\D/g, '');
  if (!digits) return '';
  const n = Number(digits) / 100;
  return n.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};
```

## Dates

```js
// Format: Date | string → "30/04/2025"
export const brDate = (d) => {
  if (!d) return '';
  const date = typeof d === 'string' ? new Date(d) : d;
  if (isNaN(date.getTime())) return '';
  return date.toLocaleDateString('pt-BR');
};

// Format: Date | string → "30/04/2025 14:32"
export const brDateTime = (d) => {
  if (!d) return '';
  const date = typeof d === 'string' ? new Date(d) : d;
  if (isNaN(date.getTime())) return '';
  return `${date.toLocaleDateString('pt-BR')} ${date.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })}`;
};

// Parse: "30/04/2025" → Date
export const parseBrDate = (s) => {
  if (!s) return null;
  const [dd, mm, yyyy] = s.split('/');
  if (!dd || !mm || !yyyy) return null;
  const d = new Date(Number(yyyy), Number(mm) - 1, Number(dd));
  return isNaN(d.getTime()) ? null : d;
};

// ISO for <input type="date"> (YYYY-MM-DD)
export const toInputDate = (d) => {
  if (!d) return '';
  const date = typeof d === 'string' ? new Date(d) : d;
  if (isNaN(date.getTime())) return '';
  return date.toISOString().slice(0, 10);
};
```

## CPF / CNPJ

```js
// Format: "12345678900" → "123.456.789-00"
export const formatCPF = (s) => {
  const d = String(s || '').replace(/\D/g, '').slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
};

// Format: "12345678000190" → "12.345.678/0001-90"
export const formatCNPJ = (s) => {
  const d = String(s || '').replace(/\D/g, '').slice(0, 14);
  if (d.length <= 2) return d;
  if (d.length <= 5) return `${d.slice(0, 2)}.${d.slice(2)}`;
  if (d.length <= 8) return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5)}`;
  if (d.length <= 12) return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8)}`;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
};

// Auto-detect CPF vs CNPJ based on length
export const formatDoc = (s) => {
  const d = String(s || '').replace(/\D/g, '');
  return d.length <= 11 ? formatCPF(d) : formatCNPJ(d);
};

// Validation (checksum)
export const isValidCPF = (s) => {
  const d = String(s || '').replace(/\D/g, '');
  if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false;
  let sum = 0;
  for (let i = 0; i < 9; i++) sum += Number(d[i]) * (10 - i);
  let r = (sum * 10) % 11;
  if (r === 10) r = 0;
  if (r !== Number(d[9])) return false;
  sum = 0;
  for (let i = 0; i < 10; i++) sum += Number(d[i]) * (11 - i);
  r = (sum * 10) % 11;
  if (r === 10) r = 0;
  return r === Number(d[10]);
};

export const isValidCNPJ = (s) => {
  const d = String(s || '').replace(/\D/g, '');
  if (d.length !== 14 || /^(\d)\1{13}$/.test(d)) return false;
  const calc = (len) => {
    const weights = len === 12
      ? [5,4,3,2,9,8,7,6,5,4,3,2]
      : [6,5,4,3,2,9,8,7,6,5,4,3,2];
    let sum = 0;
    for (let i = 0; i < len; i++) sum += Number(d[i]) * weights[i];
    const r = sum % 11;
    return r < 2 ? 0 : 11 - r;
  };
  return calc(12) === Number(d[12]) && calc(13) === Number(d[13]);
};
```

## Percent

```js
// Format: 0.8547 → "85,47%" (or 85.47 → "85,47%" depending on input scale)
export const brPercent = (n, { scale = 'ratio', digits = 2 } = {}) => {
  if (n === null || n === undefined || n === '') return '';
  const val = scale === 'ratio' ? n * 100 : n;
  return `${val.toLocaleString('pt-BR', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}%`;
};
```

## Phone

```js
// Format: "11987654321" → "(11) 98765-4321"
export const formatPhone = (s) => {
  const d = String(s || '').replace(/\D/g, '').slice(0, 11);
  if (d.length <= 2) return d;
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
  if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
};
```

---

## Usage pattern in input components

```jsx
import { brlMask, parseBrl } from './br-format';

function CurrencyInput({ value, onChange, ...rest }) {
  return (
    <input
      inputMode="decimal"
      value={value === '' ? '' : brl(value, { withSymbol: false })}
      onChange={(e) => onChange(parseBrl(e.target.value))}
      {...rest}
    />
  );
}
```

For masked-while-typing behavior:

```jsx
function CurrencyMaskedInput({ value, onChange }) {
  const [display, setDisplay] = useState('');

  const handleChange = (e) => {
    const masked = brlMask(e.target.value);
    setDisplay(masked);
    onChange(parseBrl(masked));
  };

  return <input inputMode="decimal" value={display} onChange={handleChange} />;
}
```
