/**
 * URL base do backend FastAPI.
 * Defina no .env: VITE_API_BASE=https://api.exemplo.com
 * Build Docker: docker compose build --build-arg VITE_API_BASE=...
 */
const raw = import.meta.env.VITE_API_BASE;
export const API_BASE =
  (typeof raw === 'string' && raw.trim() !== '' ? raw.trim().replace(/\/$/, '') : null) ||
  'http://127.0.0.1:8000';
