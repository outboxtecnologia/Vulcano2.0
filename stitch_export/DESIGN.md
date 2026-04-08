```markdown
# Design System Strategy: Tectonic Precision

## 1. Overview & Creative North Star
The visual identity of this system is defined by the **"Tectonic Precision"** North Star. We are moving away from the generic "SaaS dashboard" look to create an experience that feels as solid as a structural beam and as precise as a financial audit. 

This design system serves the construction accounting sector—an industry built on heavy materials and razor-sharp margins. To reflect this, we utilize **Industrial Brutalism** refined by **High-Tech Editorial** layouts. We break the traditional grid through intentional asymmetry: heavy, left-aligned typography contrasted with expansive, airy data visualizations. The interface should feel like a high-end architectural blueprint: structural, authoritative, and sophisticated.

---

## 2. Color Philosophy: The Volcanic Palette
Our palette transitions from the cold, solid strength of obsidian to the controlled energy of molten heat. 

*   **Foundation:** The core experience is anchored in `surface` (#131314) and `surface-container-lowest` (#0e0e0f). This deep charcoal base reduces eye strain during long hours of data entry.
*   **The "No-Line" Rule:** Sectioning must never be achieved with 1px solid borders. Boundaries are defined strictly through background shifts. For example, a sidebar in `surface-container-low` sits against a `surface` main content area. Use the tonal difference to guide the eye, not a line.
*   **Surface Hierarchy & Nesting:** Treat the UI as layers of physical material. 
    *   Primary workspace: `surface`
    *   Secondary modules: `surface-container-low`
    *   High-focus cards (Calculations/Summary): `surface-container-high`
*   **The Glass & Gradient Rule:** For "Floating" elements like modals or popovers, use `surface-container-highest` with a 80% opacity and a `20px` backdrop-blur. Apply a subtle linear gradient from `primary` (#ffb5a0) to `primary-container` (#ff5625) only on critical action elements to simulate a "glowing" industrial indicator.

---

## 3. Typography: Technical Authority
We pair two distinct typefaces to balance industrial character with financial legibility.

*   **Headlines (Space Grotesk):** This is our "Industrial" voice. The geometric, slightly quirky terminals of Space Grotesk (from `display-lg` to `headline-sm`) evoke engineering and blueprints. Use this for page titles and major section headers to establish authority.
*   **Data & Body (Inter):** For the "Tech" voice, Inter provides maximum legibility for high-density numerical data. Its neutral stance ensures that complex accounting tables remain readable.
*   **Editorial Scaling:** Use high contrast in sizes. Pair a `display-sm` (2.25rem) header with a `label-sm` (0.6875rem) sub-header in `on-surface-variant` to create a sophisticated, magazine-like hierarchy.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are too "soft" for an industrial aesthetic. We achieve depth through **Material Stacking**.

*   **The Layering Principle:** Instead of shadows, use the `surface-container` tiers. A `surface-container-lowest` card placed on a `surface-container-low` background creates a "inset" look, perfect for data input zones.
*   **Ambient Shadows:** Where floating is required (e.g., Tooltips), use a shadow color tinted with our `surface-tint` (#ffb5a0) at 5% opacity. The blur should be large (`16px`) to mimic a soft glow rather than a harsh shadow.
*   **The "Ghost Border":** For form fields or cards that require a boundary for accessibility, use the `outline-variant` token (#5d4038) at **20% opacity**. It should be felt, not seen.
*   **Glassmorphism:** Apply to navigation bars. Use `surface` at 70% opacity with a heavy backdrop-blur. This ensures the "volcanic" depth is always visible as the user scrolls through dense construction data.

---

## 5. Components: Engineered for Performance

### Tables & Data Grids (The System Core)
*   **Structure:** Prohibit divider lines. Use `spacing-2` (0.4rem) between rows and alternate background colors using `surface` and `surface-container-low`.
*   **Header:** Use `label-md` in all-caps with `primary` color accents for sortable columns.
*   **Density:** Keep vertical padding tight (`spacing-2`) but horizontal padding generous (`spacing-5`) to allow numbers to breathe.

### Buttons: High-Visibility Actuators
*   **Primary:** Background: `primary-container` (#ff5625); Text: `on-primary-container`. Use `rounded-sm` (0.125rem) for a sharp, machined look.
*   **Secondary:** Background: `secondary-container`; Text: `on-secondary-container`. 
*   **State:** On hover, apply a subtle inner glow using a 1px `primary` border at 30% opacity.

### Inputs & Forms
*   **Field Style:** Use "Surface-Level" inputs. Background: `surface-container-lowest`. No border, only a bottom-weighted `outline` when focused.
*   **Labels:** Always use `label-sm` floating above the input, never placeholder text alone.

### Chips & Status Indicators
*   **Status:** Use `tertiary` (#a3c9ff) for "In Progress" and `error` (#ffb4ab) for "Over Budget." 
*   **Shape:** Use `rounded-full` for chips to contrast against the sharp `rounded-sm` corners of the primary UI.

---

## 6. Do’s and Don’ts

### Do:
*   **Do** use `spacing-10` and `spacing-12` to separate major content blocks. Space is a luxury that makes dense data feel manageable.
*   **Do** align all numerical data to the right in tables to allow for immediate decimal comparison.
*   **Do** use the `primary` (Lava) color sparingly. It should represent "Action" or "Critical Alert," not decoration.

### Don’t:
*   **Don't** use `rounded-xl` or `rounded-full` for primary containers. It breaks the "Industrial" feel. Stick to `none`, `sm`, or `md`.
*   **Don't** use pure black (#000000). Always use the volcanic `surface` (#131314) to maintain tonal depth.
*   **Don't** use standard 1px borders to separate content. If the layout feels messy, increase the `spacing` scale or shift the `surface-container` tier.

---

## 7. Signature Detail: The "Machined" Edge
To add a final premium touch, use a `0.1rem` (spacing-0.5) vertical accent bar of `primary` color to the left of active navigation items or high-priority alerts. This mimics the precision of a laser-cut edge and reinforces the industrial-tech aesthetic.```