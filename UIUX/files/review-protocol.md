# Review Protocol

Use this when the user asks to revise an existing screen. Input will typically be:
- **A screenshot** (most common) — analyze it visually
- **A description in words** — reconstruct the layout mentally from the description
- **Code (JSX + CSS)** — less common, but possible

**Do not rewrite the screen.** The goal of a review is to identify specific, measurable productivity violations and propose targeted fixes. Rewriting is only appropriate if the user explicitly asks for it after seeing the review.

---

## Output structure

Produce exactly this structure, in Portuguese:

```
## Diagnóstico

[2-3 sentences describing the screen's purpose as you understand it, and the overall impression. Be specific: "tela de conciliação por conta, layout em dashboard, ocupando viewport ~1440×900".]

## Violações

[Numbered list. For each violation: quantify it, classify it, state the productivity cost.]

1. **[NOME DA VIOLAÇÃO]** — [severity: alta/média/baixa]
   Onde: [região da tela]
   Observado: [o que está lá hoje, quantificado se possível]
   Custo: [o que o operador perde com isso]

## Correções propostas (ordenadas por impacto)

[Numbered list of fixes. Each fix addresses one or more violations. Order by productivity impact (most painful first), not by difficulty.]

1. [Fix]
   → Resolve violações: #1, #3
   → Ganho estimado: [rows visíveis a mais / cliques a menos / tempo por registro]

## O que NÃO vou mexer

[Things that might look off but are fine. Call this out explicitly so the user knows it was considered, not overlooked.]
```

---

## Violations checklist — go through each in order

### Viewport & density

- [ ] **Espaço vazio medível.** Is there any contiguous region > 20% of viewport height with no data? Call it out with approximate percentage.
- [ ] **Rows visíveis.** How many data rows are visible at once? If fewer than 20 in a 900px viewport, violation.
- [ ] **Altura de linha.** Are rows taller than 32px without a reason? Measure.
- [ ] **Padding excessivo.** Any container with padding > 12px on operational content?
- [ ] **Barras de rolagem desnecessárias.** Is there vertical scroll even though the screen has empty space? Horizontal scroll on a data table?
- [ ] **Múltiplos scrolls aninhados.** Does the user have to scroll within a scrolling container? Almost always wrong.

### Information access

- [ ] **Racional escondido.** If the screen shows calculated values, is there an obvious inline way to see the formula? If the user has to navigate elsewhere, violation.
- [ ] **Histórico escondido.** Same check for history of changes.
- [ ] **Modal para coisas que deveriam ser inline.** Any modal triggered for viewing details (not for destructive confirmation)?
- [ ] **Drawer/side panel obscurando dados.** Same problem as modal.
- [ ] **Tooltip como única fonte de verdade.** Critical data hidden in tooltips? Violation.

### Visual noise

- [ ] **Gradientes decorativos.** Any gradient that doesn't encode a value?
- [ ] **Sombras em cards.** Any drop shadow on a non-floating element?
- [ ] **Ícones decorativos.** Icons next to menu items that already have text? Icons next to buttons that already have clear text?
- [ ] **Cores puramente decorativas.** Colored backgrounds on elements where the color doesn't carry meaning?
- [ ] **Animações não-informativas.** Shimmer on loading, fade on hover without reason, bounces, etc.?

### Brazilian conventions

- [ ] **Formatação de números.** Are currency values in `R$ 1.234,56` format?
- [ ] **Datas.** Display in `dd/mm/yyyy`?
- [ ] **Documentos.** CPF/CNPJ formatted correctly?
- [ ] **Tabular nums.** Are number columns aligned (monospace or `font-variant-numeric: tabular-nums`)?
- [ ] **Sinal antes da unidade.** Negative values shown clearly (red or `-` prefix, not just minus sign buried in text)?

### Keyboard & affordances

- [ ] **Affordances para expand inline.** Clear visual cue that a row can be expanded for racional/histórico?
- [ ] **Edit-in-place.** On spreadsheet-mode screens, are cells directly editable or "click to edit"?
- [ ] **Submit buttons per row.** On mass-entry screens, is there one Save per row? (Should be one Save at the top for everything.)

---

## Classification guide

**Alta severidade:** operator loses >10 seconds per record, or has to navigate to another screen for data that should be inline, or has to scroll because of wasted space.

**Média severidade:** operator has extra friction but still gets the job done — cosmetic noise, suboptimal key column placement, inconsistent formatting.

**Baixa severidade:** style inconsistencies, minor polish, keyboard shortcuts missing.

---

## Example review

> User: [attaches the Vulcano screenshot]
> "revise essa tela, tá com muito espaço vazio"

**Diagnóstico**

Tela de conciliação contábil por conta (confronto Questor × sistema próprio), layout dashboard no viewport ~1440×900. Função: operador contábil audita divergências e visualiza o racional de cada conta. Densidade atual permite ~6 linhas de dados visíveis simultaneamente — muito abaixo do necessário para auditoria eficiente.

**Violações**

1. **Cards KPI superdimensionados** — severidade alta
   Onde: linha de KPIs no topo (Conciliação Global, Movimento Total Questor, etc.)
   Observado: cards ocupam ~140px de altura cada; label, valor e espaço vazio.
   Custo: ~80px de altura desperdiçada por card × 4 cards = espaço para 10 linhas de dados a mais.

2. **Linhas de grid muito altas** — severidade alta
   Onde: tabela "Confronto por Conta"
   Observado: cada linha expandida (APTO 302, APTO 305…) consome ~120px mostrando dois sub-blocos com padding generoso.
   Custo: operador vê ~5 contas simultaneamente; em auditoria mensal com 50-100 contas, são 10-20 scrolls.

3. **Barra de rolagem horizontal no grid principal** — severidade alta
   Onde: área de dados (as colunas Questor / VU 1.0 / VU 2.0 / Status Final não cabem no viewport).
   Custo: operador perde contexto ao rolar horizontalmente; impossível comparar fontes visualmente.

4. **Sidebar ocupa ~200px sem densidade** — severidade média
   Onde: coluna esquerda com menu "Core Modules / Enterprise Suite".
   Observado: ícones + texto em linhas altas, ~30 itens visíveis.
   Custo: 14% do width horizontal usado para navegação que poderia ser colapsável.

5. **Status pills coloridos grandes ("DIVERGENTE")** — severidade baixa
   Onde: cada linha.
   Observado: pill com background sólido, padding generoso.
   Custo: ruído visual; "● DIVERGENTE" textual seria suficiente.

**Correções propostas**

1. **Colapsar KPIs para 64px de altura.** Label de 11px acima, valor mono de 20px abaixo, sem padding interno além de 8px vertical. → Resolve #1 → Ganho: +10 linhas visíveis.

2. **Unificar o grid em uma linha por conta.** Os blocos separados Questor / VU 1.0 / VU 2.0 viram colunas na mesma linha, com affordance `ƒ` para expandir racional inline quando divergente. → Resolve #2, #3 → Ganho: +15 linhas visíveis, sem scroll horizontal.

3. **Sidebar colapsável default icon-only (48px).** Expande para 200px ao hover ou via atalho. → Resolve #4 → Ganho: +150px horizontal para dados.

4. **Pills → texto + bullet colorido.** `● DIVERGENTE` em 11px. → Resolve #5.

**O que NÃO vou mexer**

- Paleta de cores (preto + laranja/magenta/cyan) está coerente com a marca Vulcano e funciona para densidade — mantém.
- Botões "Auditar" e "Diagnóstico IA" no topo estão certos como primários/secundários — mantém.
- Localização do filtro de período no topo esquerdo — é onde o olho espera, mantém.
