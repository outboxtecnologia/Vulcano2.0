# Design System Document: Precision Industrialism

## 1. Overview & Creative North Star
**The Creative North Star: "The Technical Manuscript"**

This design system rejects the "web-template" aesthetic in favor of a high-end, editorial approach to industrial data management. It draws inspiration from mid-century technical manuals and architectural blueprints—environments where precision is paramount, but clarity is achieved through white space rather than clutter.

The system breaks the traditional digital grid by utilizing **monochromatic dominance** and **extreme starkness**. By leveraging a "Technical Manuscript" philosophy, we treat data entry as a high-stakes drafting process. We avoid standard UI tropes (like heavy borders and drop shadows) and instead use **intentional asymmetry** and **tonal layering** to guide the eye. The result is a workspace that feels expensive, authoritative, and purposefully quiet, allowing the user to focus on complex report analysis without visual fatigue.

---

## 2. Colors & Surface Philosophy

### The Palettes
- **Primary (#5E5E5E / #323232):** Our "Ink." Used for primary actions and high-contrast text. While the brand feels black, we use varying shades of deep charcoal to prevent "eye-vibration" on pure white surfaces.
- **Secondary (#B22E00 / #FF4500):** Our "Warning & Action." This is used sparingly—like a red pen mark on a technical drawing—to highlight critical data points or primary call-to-actions.
- **Neutrals (#F9F9F9 to #FFFFFF):** Our "Paper." The foundation of the system.

### The "No-Line" Rule
Traditional 1px borders are strictly prohibited for sectioning. Structural boundaries must be defined solely through background color shifts. For example, a sidebar in `surface_container_low` (#F3F3F3) sits flush against a main content area in `surface` (#F9F9F9). This creates a "seamless" interface that feels like a single, cohesive tool rather than a collection of boxes.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked, physical sheets of fine paper:
- **Level 0 (Base):** `surface` (#F9F9F9)
- **Level 1 (Nesting):** `surface_container_low` (#F3F3F3) for secondary navigation or grouping.
- **Level 2 (Active Highlighting):** `surface_container_highest` (#E2E2E2) for focused input areas.

### The "Glass & Gradient" Rule
To add soul to the industrial starkness, floating modals and menus should utilize **Glassmorphism**. Use `surface_container_lowest` (#FFFFFF) at 80% opacity with a `20px` backdrop-blur. Main CTAs may use a subtle linear gradient from `secondary` (#B22E00) to `secondary_dim` (#9D2700) to provide a tactile, premium depth.

---

## 3. Typography: The Editorial Scale

We pair the geometric precision of **Space Grotesk** with the utilitarian readability of **Inter**.

- **Display & Headlines (Space Grotesk):** These are our "Brand Anchors." Space Grotesk should be used for large titles (`display-lg` at 3.5rem) and section headers. Use tight letter-spacing (-0.02em) to give it a modern, architectural feel.
- **Body & Titles (Inter):** Used for data entry and long-form analysis. Inter provides the neutral, legible counterpoint to the expressive Space Grotesk.
- **Labels (Space Grotesk):** For metadata and small captions, we revert to Space Grotesk (`label-md` at 0.75rem) in all-caps with increased letter-spacing (+0.05em) to mimic industrial stamping.

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved through **Tonal Layering** rather than structural lines.
*   **Action:** To lift a card, do not add a border. Shift its background from `surface` (#F9F9F9) to `surface_container_lowest` (#FFFFFF). The subtle contrast creates a natural "lift."

### Ambient Shadows
Shadows are reserved only for elements that physically "float" (e.g., Tooltips, Popovers).
*   **Spec:** `box-shadow: 0 10px 30px rgba(50, 50, 50, 0.06);`
*   The shadow color is a tinted version of `on_surface`, creating a soft, ambient glow rather than a muddy grey drop.

### The "Ghost Border" Fallback
If a border is required for accessibility in complex data grids, use a **Ghost Border**:
*   **Spec:** `outline_variant` (#B22E00) at **15% opacity**. It should be felt, not seen.

---

## 5. Components

### Buttons
- **Primary:** Solid `on_surface` (#323232) background with `on_primary` (#F8F8F8) text. Sharp 0px corners.
- **Secondary:** Transparent background with a `ghost border` and Space Grotesk text.
- **Tertiary:** Text-only, using `secondary` (#B22E00) for "Action" calls.

### Cards & Lists
- **Rule:** Absolute prohibition of divider lines.
- **Execution:** Use vertical white space (`spacing.8` or `1.75rem`) to separate list items. For cards, use a background shift to `surface_container_low` on hover to indicate interactivity.

### Input Fields
- **Default State:** Underline only (2px `outline_variant`). No four-sided boxes. 
- **Focus State:** Underline transitions to `primary` (#5E5E5E) with a subtle `surface_container_highest` background fill.
- **Error State:** Underline transitions to `secondary` (#B22E00).

### Additional Component: The "Data Monolith"
For industrial reporting, use a custom "Data Monolith" component—a large, high-contrast block using `display-sm` for a single metric, paired with a small `label-sm` Space Grotesk tag above it. This creates an authoritative "dashboard" look that emphasizes key KPIs.

---

## 6. Do’s and Don'ts

### Do:
*   **Do** use extreme white space. If a layout feels "empty," it is likely working.
*   **Do** use `0px` border-radius for every single element. This is a non-negotiable brand signature.
*   **Do** use `secondary` (#FF4500/B22E00) only for the most important interactive elements. It is a "laser pointer," not a decorative color.

### Don’t:
*   **Don’t** use 1px solid black borders to separate content. Use background tonal shifts.
*   **Don’t** use standard "Blue" for links. All interactive elements are either `on_surface` (Black/Grey) or `secondary` (Orange/Red).
*   **Don’t** add "Rounded" corners even if requested for "friendliness." This system is built on industrial precision, not softness.