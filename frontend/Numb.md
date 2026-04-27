# Design System Document: The Industrial Archive

## 1. Overview & Creative North Star: "The Industrial Archive"
This design system is a sophisticated homage to the era of high-density, reliable desktop computing. It moves beyond mere "retro" aesthetics to establish a **Creative North Star of "The Industrial Archive."** 

Unlike modern "airy" interfaces that sacrifice information density for white space, this system embraces the authoritative weight of legacy accounting software (Delphi/Windows Classic). It treats the UI as a physical workstation—a precision tool forged from neutral alloys and glass. We break the "template" look through a strict 0px radius policy, creating a rhythmic, architectural grid where depth is communicated through light and shadow (beveling) rather than flat strokes. The result is a signature editorial experience that feels permanent, reliable, and intentional.

## 2. Colors
Our palette is a study in tonal grey, punctuated by the high-vis intensity of "Magma Orange."

- **The Neutral Foundation:** We utilize `surface`, `surface-container-low`, and `surface-container-highest` to build the "chassis" of the application. These neutral tones (#C0C0C0, #D4D0C8) are not merely backgrounds; they are the material of the tool.
- **The "No-Line" Rule:** Explicitly prohibit the use of 1px solid borders for sectioning. Structural boundaries must be defined solely through background color shifts or 3D beveling effects. For example, a toolbar should sit on `surface-bright` while the main workspace occupies `surface-container-low`.
- **Magma Orange (#FF4500):** This is our "Industrial Heat." It is reserved strictly for primary actions (`primary`) and the brand mark. It should feel like a physical warning or an energized component within a cold machine.
- **The "Glass & Gradient" Rule:** While the aesthetic is industrial, floating modals and high-level tooltips should utilize a semi-transparent `surface` with a heavy backdrop-blur. This "frosted glass" effect prevents the dense UI from feeling claustrophobic, allowing the complex data below to peek through the active layer.
- **Signature Textures:** Use subtle linear gradients (transitioning from `primary` to `primary_container`) on large action buttons to mimic the slight convex curve of a physical plastic button.

## 3. Typography
Typography is the engine of "The Industrial Archive." We utilize **Inter** for its neutral, high-legibility characteristics, but we apply it with editorial hierarchy.

- **Display & Headline:** Used sparingly. These should feel like "Document Titles" or "Ledger Headers." High-contrast scaling between `display-lg` and `body-sm` creates an authoritative hierarchy.
- **Body & Label:** The workforce of the system. We prioritize `body-sm` (0.75rem) and `label-sm` (0.6875rem) to maintain high data density. 
- **Functional Clarity:** Labels are often paired with "Magma Orange" icons in the toolbar, creating a visual shorthand that rewards power users.

## 4. Elevation & Depth: The Bevel Logic
In this system, elevation is not achieved through shadows, but through **Tonal Layering and Skeuomorphic Beveling.**

- **The Layering Principle:** Depth is "carved" into the UI. Use `surface-container-lowest` (White) for input fields to make them appear "inset" into the `surface` (Grey). 
- **The 3D Bevel:** 
    - **Raised Elements (Buttons):** Top and left edges use `surface-bright`; bottom and right edges use `surface-dim`.
    - **Recessed Elements (Fields):** Top and left edges use `surface-dim`; bottom and right edges use `surface-bright`.
- **Ambient Shadows:** For floating elements (like Context Menus), use a tinted shadow derived from `on-surface` at 8% opacity with a large 32px blur. This mimics ambient occlusion rather than a direct light source.
- **The "Ghost Border" Fallback:** If a separator is required for accessibility, use the `outline-variant` token at 15% opacity. Never use a 100% opaque border.

## 5. Components

### Buttons
- **Primary (Magma Orange):** 0px radius. 3D raised bevel. White text (`on-primary`). 
- **Secondary (Grey):** `surface-container-highest` background. Subtle bevel. This should feel like a physical part of the frame.
- **Tertiary:** No background. `primary` text. Used for low-emphasis utility actions.

### Input Fields
- **Architecture:** Must be `surface-container-lowest` (White) background.
- **Border:** Inset bevel effect using `surface-dim` on the top/left interior.
- **State:** On focus, the interior "Ghost Border" shifts to `primary` (Magma Orange) at 20% opacity.

### Toolbars & Iconography
- **Density:** Icons should be 16x16 or 20x20.
- **Visuals:** Use high-saturation, multi-color icons (Legacy Delphi style) to provide instant functional recognition against the neutral grey backdrop.
- **Container:** Sitting on `surface-bright` to provide a "shelf" for the tools.

### Lists & Data Grids
- **Rules:** Forbid divider lines. Use alternating row colors (`surface` and `surface-container-low`) to guide the eye.
- **Header:** `surface-container-highest` with a distinct raised bevel to separate the "Actionable Header" from the "Data Row."

### Chips
- **Style:** Rectangular (0px radius). Use `secondary-container` for the background. They should look like small, physical tabs or labels stuck onto a folder.

## 6. Do's and Don'ts

### Do
- **Do** prioritize information density. This tool is for professionals, not casual browsing.
- **Do** use 0px radius for every single element. 1px of rounding breaks the industrial illusion.
- **Do** use `Magma Orange` with extreme restraint. It is a "Heat Map" for the user's attention.

### Don't
- **Don't** use standard drop shadows. Rely on color shifts and bevels.
- **Don't** use 100% black text. Use `on-surface` (#1D1C17) for a more natural, ink-on-metal look.
- **Don't** use rounded icons. All iconography should feel sharp and pixel-perfect.
- **Don't** introduce "Airy" padding. Maintain tight, 4px/8px increments to keep the UI feeling like a high-density professional instrument.