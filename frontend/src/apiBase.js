/**
 * URL base do backend FastAPI.
 * Defina no .env: VITE_API_BASE=https://api.exemplo.com
 * Build Docker: docker compose build --build-arg VITE_API_BASE=...
 */
const raw = import.meta.env.VITE_API_BASE;
// Default '': mesma origem de onde a SPA foi servida (backend serve o dist).
// Em dev (Vite standalone) defina VITE_API_BASE apontando pro backend.
export const API_BASE =
  (typeof raw === 'string' && raw.trim() !== '' ? raw.trim().replace(/\/$/, '') : null) ||
  '';
