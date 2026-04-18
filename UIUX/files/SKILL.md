---
name: antigravity-ui-operational
description: Build and review React UI components optimized for high information density and operator productivity - dashboards for reconciliation and fiscal/accounting calculations (racional), mass data-entry screens styled as editable spreadsheets, and audit/review interfaces for Brazilian accounting/ERP systems. Use this skill whenever the user asks to "crie um campo", "crie uma tela", "crie um componente", "revise essa tela", "revise esse campo", "monta o dashboard de X", "tela de lançamento de X", "tela de conciliação", or attaches a screenshot of a UI and asks for improvements. Use it even when the user just says "componente React" or "tela" in the context of the Arquivo/Vulcano/Daccta projects. The skill enforces dense, productivity-first layouts (Linear + GitHub + Nothing aesthetic) using React + Vite + Vanilla CSS with no Tailwind and no component libraries. Always use this skill over generic React generation for operator-facing screens.
---

# Antigravity UI — Operational Density Skill

Build React components for **power-users who process hundreds of records per day**. The operator is not browsing — they are *working*. Every pixel either helps them work or wastes their time.

**Stack:** React + Vite + Vanilla CSS. No Tailwind. No shadcn. No Material UI. No component libraries. CSS written by hand using the tokens below.

**Aesthetic references:** Linear (density + keyboard-first), GitHub (dense lists, readable), Nothing Tech (honest, no decoration). NOT: Stripe dashboards, Vercel landing pages, generic SaaS cards.

---

## Mode detection

The user will be in one of two modes. Detect which and act accordingly.

### Mode 1 — CREATION
Triggers: "crie um campo", "crie uma tela", "crie um componente", "monta o dashboard", "tela de lançamento de X", "componente pra mostrar Y".

Action: Generate the component following all rules below. Default to the two canonical templates (see `references/templates.md`).

### Mode 2 — REVIEW
Triggers: "revise essa tela", "revise esse campo", user attaches a screenshot, user describes an existing screen with complaints ("tem muito espaço vazio", "tá com barra de rolagem", "o operador tem que ficar clicando").

Action: Do NOT rewrite the whole screen. Follow the review protocol in `references/review-protocol.md` — identify specific violations, quantify them (e.g. "40% do viewport é espaço vazio"), propose targeted fixes ordered by productivity impact.

---

## Hard rules (non-negotiable)

These are the rules. Violating them is a bug, not a style choice.

### Density rules

1. **No vertical dead space.** Maximum `padding` on operational containers is **12px**. Maximum `gap` between related fields is **8px**. Maximum `margin` between sibling sections is **16px**. If the screen fits in 80% of viewport height, fill the other 20% with more data or a secondary panel — never with air.

2. **No horizontal scroll on tables of record.** If columns don't fit, reduce padding first, shrink font to `12px` second, sticky-freeze the key column third, hide decorative columns fourth. Horizontal scroll is a last resort and must be flagged to the user.

3. **No vertical scroll without density justification.** If a screen scrolls vertically, every visible row must be dense (`max-height: 32px` per row for lists, `max-height: 28px` for spreadsheet-mode). If rows are "comfortable height" AND the screen scrolls, that's a violation.

4. **Inline details, not modals.** If the operator needs to see "why" or "history" or "racional" for a row, it expands inline (accordion-style, in-place) — not a modal, not a new screen, not a side panel that covers other data. Modals are reserved for destructive confirmations only.

5. **Viewport budget.** In a 1440×900 viewport (standard for Fernando's setup with the ASUS VG27AQ5A and Samsung OLED G8), an operational screen must show **at least 20 rows of data** without scroll, OR justify why fewer rows are needed (e.g. a wide detail row with racional calculation visible).

### Anti-decoration rules

6. **No gradients.** Solid colors only. The one exception: the progress bar on the Conciliação Global card can use a 2-stop gradient because it encodes a value.

7. **No drop shadows on cards.** Borders instead (`1px solid var(--border)`). Shadow is reserved for floating elements (dropdowns, the one modal you're allowed).

8. **No decorative icons.** Icons only appear if they encode meaning that text can't carry faster — status (●), direction (↑↓), action affordance (⌕ for search, × for close). No icons next to menu labels. No icons next to buttons that already have clear text.

9. **No skeleton loaders that shimmer.** Use a plain text "Carregando…" or a static muted block. Shimmer animations waste attention on a working screen.

10. **No rounded corners > 4px.** `border-radius: 4px` maximum on buttons and inputs. `0px` on table cells and panel borders. Rounded = decorative; operational = sharp.

### Information rules

11. **Every number shows its unit and sign immediately.** `R$ 129.615,63 C` (C = crédito, D = débito — one letter, not a word). Negative values in red, positive in the neutral text color (not green — green is reserved for "OK/validated" status, not for positive numbers).

12. **Brazilian formatting is the default, not a feature.**
    - Currency: `R$ 1.234.567,89` (dot thousands, comma decimal)
    - Dates: `30/04/2025` for display, `2025-04-30` only in `<input type="date">`
    - CPF: `123.456.789-00`, CNPJ: `12.345.678/0001-90`
    - No toggle, no i18n, no locale prop. Just BR.

13. **Status is a color AND a word.** Never color-only. `● DIVERGENTE` not just `●`. Never rely on color alone to convey state (basic accessibility, but also: colorblind operators exist).

14. **Racional inline.** Any calculated value in a dashboard must have a way to see its formula/components *inline, in place*. Pattern: a small `ƒ` or `?` affordance at the end of the cell that expands a row below showing the calculation breakdown. Never send the operator to another screen for "how was this computed".

15. **History inline.** Any record that has a history of changes shows a `⟳` affordance that expands an inline timeline row. Same pattern as racional.

---

## Spreadsheet mode (mass data entry)

When the user asks for a "tela de lançamento", "tela de lançamentos em massa", "entrada de dados", or similar with volume implied, generate a **spreadsheet-style editable grid**. Rules:

- Cells are `<input>` elements directly, not "click to edit". Always editable.
- Row height: `28px` max.
- Cell padding: `4px 8px`.
- `Tab` moves right, `Shift+Tab` moves left, `Enter` moves down, `Shift+Enter` moves up. Arrow keys work too.
- `Ctrl+D` duplicates the row above into the current row (Excel fill-down).
- Validation happens on blur, error shown as a red left-border on the cell + a tooltip on hover. Never a modal, never a toast for field-level errors.
- First column is a row number + a row-action affordance (×  to delete, ⎘ to duplicate). Sticky.
- Totals row at the bottom, sticky. Shows sum/count/mean for numeric columns.
- "Adicionar linha" button at the bottom-left, but `Enter` on the last row also creates a new row below (Excel behavior).
- No "Save" button per row. Either autosave (debounce 500ms) or a single "Salvar tudo" at the top-right showing `N alterações não salvas`.

Full spreadsheet component template in `references/templates.md` → "Spreadsheet Mode".

---

## Dashboard mode (conciliation + racional)

When the user asks for a "dashboard", "tela de conciliação", "confronto", "auditoria", generate a dense dashboard with these zones:

1. **Filter bar (top, 48px tall max).** Period, entity selector, toggles. No "Apply" button — filters apply on change with a 300ms debounce.
2. **KPI row (64px tall max).** 4-6 metric cards in a single row. Each card: label on top (11px, uppercase, muted), value below (20px, bold, monospace), optional delta (11px, colored). No icons on cards.
3. **Main grid (fills remaining viewport).** The actual confronto/conciliação table. Dense rows, inline expand for divergences showing racional.
4. **Status legend (bottom, 24px tall).** Color key for status indicators. Sticky.

No sidebars stealing horizontal space unless the user has one already. If a sidebar exists in the screenshot, keep it but compress it: icon-width (48px) collapsible by default.

Full dashboard template in `references/templates.md` → "Dashboard Mode".

---

## Design tokens (derived from the Vulcano screenshot)

Use these exact CSS variables. Put them in a `:root` block at the top of the component's CSS file, or in a shared `tokens.css`.

```css
:root {
  /* Surfaces */
  --bg-app: #0a0a0a;
  --bg-panel: #141414;
  --bg-panel-hover: #1a1a1a;
  --bg-cell: #0f0f0f;
  --bg-cell-edit: #1a1a1a;

  /* Borders */
  --border: #262626;
  --border-strong: #363636;
  --border-focus: #ff6b1a;

  /* Text */
  --text: #e8e8e8;
  --text-muted: #8a8a8a;
  --text-dim: #5a5a5a;

  /* Status — meaning-carrying colors, use sparingly */
  --status-ok: #22c55e;        /* green — validated */
  --status-divergent: #ff6b1a; /* orange — divergent, needs attention */
  --status-warn: #eab308;      /* yellow — partial, in progress */
  --status-error: #ef4444;     /* red — error, negative values */
  --accent-questor: #22c55e;   /* ERP source A */
  --accent-system: #c026d3;    /* ERP source B (magenta from Vulcano) */
  --accent-diff: #eab308;      /* divergence indicator */

  /* Action */
  --action: #ff6b1a;
  --action-hover: #ff8540;
  --action-secondary: #00bcd4; /* cyan secondary action */

  /* Typography */
  --font-sans: -apple-system, 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
  --fs-xs: 11px;
  --fs-sm: 12px;
  --fs-base: 13px;
  --fs-lg: 16px;
  --fs-xl: 20px;

  /* Spacing — intentionally small */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-5: 24px;

  /* Radii */
  --r-none: 0;
  --r-sm: 2px;
  --r-md: 4px;

  /* Timings */
  --t-fast: 80ms;
  --t-base: 150ms;
}
```

Numbers always use `font-family: var(--font-mono)` and `font-variant-numeric: tabular-nums` so columns of numbers align.

---

## Output format

When generating a component (CREATION mode), output in this order:

1. **One-line summary** of what you built and the key density decision (e.g. "Tela de conciliação densa, 24 linhas visíveis no viewport, racional expansível inline").
2. **Component file** — `ComponentName.jsx` (single file, all logic).
3. **Styles file** — `ComponentName.css` (uses tokens, no inline styles except for dynamic values like progress width).
4. **Tokens file** — only if this is the first component or if tokens changed. Otherwise reference `tokens.css`.
5. **Brief rationale (max 5 bullets)** — what you optimized for, any tradeoffs, what you'd need to know to go further. No walls of text.

When reviewing (REVIEW mode), follow `references/review-protocol.md` — the output is an audit, not a rewrite.

---

## Preview

After generating, always include instructions for preview:

```
# No seu projeto Vite:
cp ComponentName.jsx src/components/
cp ComponentName.css src/components/
# Importe onde quiser testar. Para preview isolado, crie src/pages/PreviewComponentName.jsx.
```

If the user is running the skill inside Antigravity's sandbox and a preview environment is available, render the component directly.

---

## References — read when needed

- `references/templates.md` — Full code templates for Dashboard Mode and Spreadsheet Mode. **Read this before generating any component** to save re-deriving structure.
- `references/review-protocol.md` — Step-by-step audit checklist for REVIEW mode. Read this when user asks to revise a screen or attaches a screenshot.
- `references/anti-patterns.md` — Gallery of things NOT to do, with explanations. Read when unsure whether a pattern is acceptable.
- `references/br-formatting.md` — Utility functions and regex for Brazilian formatting (currency, dates, CPF/CNPJ, percent). Copy-paste these into components that need them.

---

## Nice-to-haves (not required, but appreciated)

- Keyboard shortcuts on operational screens. If you add them, document them in a `<kbd>` legend at the bottom of the screen, `11px`, muted. Common ones: `/` focuses search, `Esc` cancels edit, `Ctrl+S` saves, `Ctrl+Enter` confirms. Never add a shortcut without visible documentation.
- Column width persistence via `localStorage` for spreadsheet-mode tables.
- A "compact / comfortable" toggle — but **compact is the default**. Comfortable mode just adds 4px to row height.

---

## What this skill is NOT for

- Marketing landing pages (Daccta B2B pages) — those are a different aesthetic, different skill.
- Client-facing consumer UIs — operators are the audience, not end-customers.
- Mobile-first designs — operational screens live on desktop. If mobile is required, flag to the user that density rules change.
- Presentation decks, PDFs, infographics — use other skills.
