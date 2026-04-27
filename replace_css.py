import re

with open('frontend/src/index.css', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace everything after utilities
idx = text.find('@tailwind utilities;')
if idx != -1:
    text = text[:idx + len('@tailwind utilities;')] + "\n\n"

new_css = """/* ============================================================
   THEME ROOTS AND COLOR PALETTES
   ============================================================ */

/* NIGHT THEME (Padrão) - Tectonic Precision */
:root, [data-theme="night"] {
  --v-bg: #131314;     /* Surface */
  --v-deep: #0e0e0f;   /* Surface-container-lowest */
  --v-card: #18191a;   /* Surface-container-low */
  --v-hover: #1e1e1f;  /* Interactive hover */
  --v-muted: #272728;  /* Background dividers */
  --v-border: #333334; /* Lines */
  
  --v-text: #e0e0e0;
  --v-text-bold: #ffffff;
  --v-text-muted: #888888;
  --v-text-faint: #5d5d5e;
  --v-text-inv: #000000;
  
  --v-accent: #ff5625;   /* Primary */
  --v-accent-2: #ffb5a0; /* Primary container */
  --v-accent-3: #a3c9ff; /* Tertiary */
  --v-accent-4: #00c2ff; 
  --v-accent-5: #ffb4ab; /* Error */
  --v-accent-6: #ff8a00;
  
  --v-radius: 4px; /* sm */
  --v-ghost-border: rgba(93, 64, 56, 0.2);
  --v-shadow: 0 16px 32px rgba(255, 181, 160, 0.05); /* Tectonic glowing shadow */
}

/* LIGHT THEME - The Technical Manuscript */
[data-theme="light"] {
  --v-bg: #f9f9f9;     /* Surface */
  --v-deep: #ffffff;   /* Surface-container-lowest */
  --v-card: #f3f3f3;   /* Surface-container-low */
  --v-hover: #eaeaea;  
  --v-muted: #e2e2e2;  
  --v-border: #e0e0e0; 
  
  --v-text: #323232;
  --v-text-bold: #1a1a1a;
  --v-text-muted: #5e5e5e;
  --v-text-faint: #aaaaaa;
  --v-text-inv: #ffffff;
  
  --v-accent: #b22e00;   /* Secondary */
  --v-accent-2: #ff4500; 
  --v-accent-3: #228c3a;
  --v-accent-4: #005599;
  --v-accent-5: #660099;
  --v-accent-6: #885500;
  
  --v-radius: 0px; 
  --v-ghost-border: rgba(178, 46, 0, 0.15);
  --v-shadow: 0 10px 30px rgba(50, 50, 50, 0.06);
}

/* NUMB THEME - The Industrial Archive */
[data-theme="numb"] {
  --v-bg: #c0c0c0;
  --v-deep: #d4d0c8;
  --v-card: #a8a8a8;
  --v-hover: #dcdcdc;
  --v-muted: #808080;
  --v-border: #808080;
  
  --v-text: #1d1c17;
  --v-text-bold: #000000;
  --v-text-muted: #4a4a48;
  --v-text-faint: #686866;
  --v-text-inv: #ffffff;
  
  --v-accent: #ff4500;   /* Magma Orange */
  --v-accent-2: #c08000; 
  --v-accent-3: #287034;
  --v-accent-4: #0055cc;
  --v-accent-5: #660099;
  --v-accent-6: #a07800;
  
  --v-radius: 0px;
  --v-ghost-border: rgba(128, 128, 128, 0.4);
  --v-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

/* ============================================================
   ARCHITECTURAL AND BEVEL OVERRIDES 
   ============================================================ */

/* Numb Bevels (Classic Windows style 3D) */
[data-theme="numb"] .btn-3d {
  box-shadow: inset -1px -1px 0 #808080, inset 1px 1px 0 #ffffff !important;
  background-color: var(--v-deep);
}
[data-theme="numb"] .input-3d {
  box-shadow: inset 1px 1px 0 #808080, inset -1px -1px 0 #ffffff !important;
  background-color: #ffffff;
  border-radius: 0 !important;
}
[data-theme="numb"] .card-3d {
  box-shadow: inset -1px -1px 0 #808080, inset 1px 1px 0 #ffffff !important;
}

/* Force zero lines across systems when specified */
[data-theme="numb"] .border, [data-theme="light"] .border {
   /* We use tonal hierarchy instead, allowing very faint borders if absolutely necessary */
   border-color: var(--v-border) !important;
}

/* Space Grotesk Typographical overrides can be forced naturally by fonts or just let Inter serve as base */
* {
    transition: background-color 0.2s ease, border-color 0.2s ease, color 0.1s ease;
}

body {
    background-color: var(--v-bg);
    color: var(--v-text);
}
"""

text += new_css

with open('frontend/src/index.css', 'w', encoding='utf-8') as f:
    f.write(text)

print("CSS updated")
