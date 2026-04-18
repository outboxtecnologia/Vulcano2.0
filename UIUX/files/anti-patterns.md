# Anti-patterns

Things NOT to do, and why. When in doubt about a pattern, check here first.

---

## 1. Cards with drop shadows

**Bad:**
```css
.card {
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  border-radius: 12px;
  padding: 24px;
}
```

**Why it's wrong:** Shadows imply elevation. In operational UIs, nothing is elevated — everything is equally important. Shadows also add visual noise and imply a "landing page" aesthetic. Use borders instead.

**Good:**
```css
.card {
  border: 1px solid var(--border);
  padding: 8px 12px;
}
```

---

## 2. Gradient backgrounds for decoration

**Bad:**
```css
.hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

**Why it's wrong:** Gradients carry no information. They're visual decoration, which costs attention. The one exception: a two-stop gradient on a progress bar where the color encodes a value (e.g., red → green across a conciliation score).

---

## 3. Large icons next to menu labels

**Bad:**
```jsx
<a><IconDashboard size={20} /> Dashboard</a>
<a><IconOrders size={20} /> Pedidos</a>
<a><IconReports size={20} /> Relatórios</a>
```

**Why it's wrong:** The operator reads the label. The icon is redundant. If you want an icon-only collapsed mode, make it collapsible — but don't show icon + text by default.

**Acceptable:** Status icons (●), directional arrows (↑↓), action affordances (×, ⎘, ƒ, ⟳) — these encode meaning that text would slow down.

---

## 4. Modal for viewing details

**Bad:**
```jsx
<Row onClick={() => setModalContent(rowDetails)}>
  ...
</Row>
<Modal>{modalContent}</Modal>
```

**Why it's wrong:** Modals block the rest of the data. The operator loses context. They close the modal, they lose their place. If they need to compare row A with row B, modals make it impossible.

**Good:** Inline expand below the row (accordion pattern). Full context preserved.

**Modal is acceptable for:** destructive confirmations only ("Excluir 237 registros?").

---

## 5. Skeleton loaders with shimmer

**Bad:**
```jsx
{loading ? <ShimmerSkeleton /> : <Data />}
```

**Why it's wrong:** Operational screens are reloaded all the time. A shimmer animation on every reload is visual spam. A plain "Carregando…" or a muted block communicates the same thing without stealing attention.

---

## 6. Color-only status

**Bad:**
```jsx
<span style={{color: 'red'}}>●</span>
```

**Why it's wrong:** Colorblind users can't read it. More importantly: even non-colorblind operators scan by word recognition, not by color. Color + word is always faster.

**Good:** `● DIVERGENTE` — color and word.

---

## 7. "Click to edit" in spreadsheet mode

**Bad:**
```jsx
<Cell onClick={() => setEditing(true)}>
  {editing ? <input /> : <span>{value}</span>}
</Cell>
```

**Why it's wrong:** On a mass-entry screen, every cell is editable. Making the user click to enter edit mode doubles the clicks. The operator is there to type, not to prepare to type.

**Good:** Cells are `<input>` directly, always.

---

## 8. Per-row save buttons

**Bad:**
```
| Data | Conta | Valor | [Salvar] |
| Data | Conta | Valor | [Salvar] |
```

**Why it's wrong:** 100 rows = 100 save clicks. Operator will make mistakes because they'll forget which row they saved.

**Good:** Autosave (debounced) OR a single "Salvar tudo" at the top with a "N alterações não salvas" counter.

---

## 9. Tooltip as the only source of information

**Bad:**
```jsx
<span title="Cliente: HS Construtora / CNPJ: 12.345.678/0001-90">959</span>
```

**Why it's wrong:** Critical context hidden behind a hover. Operators won't hover. If it's important, show it.

**Good:** Show the data inline, or show it in an expand affordance. Tooltips are for *additional* context, not *required* context.

---

## 10. Rounded-corner everything

**Bad:**
```css
.table-cell, .button, .card, .input { border-radius: 12px; }
```

**Why it's wrong:** Rounded corners = consumer product / marketing. Operational UIs are tools. Tools have sharp edges.

**Good:** `border-radius: 4px` max on buttons/inputs, `0` on cells and panels.

---

## 11. Floating labels

**Bad:**
```
┌─────────────────┐
│ Nome            │  ← label floats inside, then jumps up on focus
└─────────────────┘
```

**Why it's wrong:** Labels that animate waste attention. In a dense form, operators need to see all labels at a glance. Static labels above the field are faster to scan.

**Good:** Label above field, always visible, 11px uppercase muted.

---

## 12. Progress bars that animate on every update

**Bad:** A progress bar that fades/animates its width transition on every data refresh.

**Why it's wrong:** If the screen refreshes every 5 seconds, the animation loops constantly.

**Good:** `transition: width 150ms` is fine for explicit user actions. For data refreshes, either skip the transition or use `will-change` carefully. And ask if the refresh needs to be that frequent at all.

---

## 13. Auto-expanding accordions on hover

**Bad:** Rows that expand their inline details on hover.

**Why it's wrong:** The operator moves the mouse across the screen while thinking. Hovering accidentally expands 10 rows, shifts the layout, loses their place.

**Good:** Expand only on explicit click of the affordance (`ƒ`, `⟳`).

---

## 14. Centered single-column forms

**Bad:**
```
            [Form field]
            [Form field]
            [Form field]
            [Submit]
```

**Why it's wrong:** Wastes horizontal space. A two- or three-column form of related fields is denser and lets the operator see everything at once.

**Good:** Multi-column layouts where related fields sit side by side. Use `grid-template-columns: 1fr 1fr 1fr` on form rows.

---

## 15. Toast notifications for field validation

**Bad:** Typing an invalid value in a cell triggers a toast "Valor inválido" in the corner.

**Why it's wrong:** The error is far from the field. The operator has to look away, read, look back, find the field again.

**Good:** Red left-border on the cell + tooltip with the reason on hover. Error stays with the field.
