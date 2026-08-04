/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  // Um sinal so de tema: data-theme. Nao ha variante `dark:` no projeto hoje, mas se
  // alguem escrever uma, ela passa a responder ao mesmo atributo.
  darkMode: ["selector", '[data-theme="dark"]'],
  theme: {
    extend: {
      // Sem paleta Material aqui: as cores do app vivem em --v-* (src/index.css)
      // e sao usadas como arbitrary values, ex. bg-[var(--v-card)].
      fontFamily: {
        "headline": ["Space Grotesk", "sans-serif"],
        "body": ["Inter", "sans-serif"],
        "label": ["Inter", "sans-serif"]
      },
      borderRadius: {"DEFAULT": "0.125rem", "lg": "0.25rem", "xl": "0.5rem", "full": "0.75rem"},
      // `border` sem cor explicita acompanha o tema, em vez do cinza do preflight.
      borderColor: { DEFAULT: "var(--v-border)" },
    },
  },
  plugins: [],
}
