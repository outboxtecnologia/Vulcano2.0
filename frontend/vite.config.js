import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Bind mount de disco Windows dentro do Docker nao propaga eventos inotify:
// sem polling o HMR nunca dispara. Ligado so quando VITE_USE_POLLING=1
// (definido no docker-compose.dev.yml), entao `npm run dev` no host segue igual.
const usePolling = process.env.VITE_USE_POLLING === '1'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: usePolling
    ? { watch: { usePolling: true, interval: 300 } }
    : undefined,
})
