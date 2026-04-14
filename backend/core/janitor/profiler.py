"""
Janitor Profiler — Middleware de timing assíncrono para FastAPI.

Registra P50/P95/P99 de cada endpoint em janitor_metrics.sqlite.
Não impacta performance: usa asyncio.Queue para writes não-bloqueantes.
"""
import time
import asyncio
import sqlite3
import os
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# ── Banco de métricas (separado do poc_database.sqlite) ───────────────────────
_JANITOR_DB = os.path.join(os.path.dirname(__file__), "..", "..", "janitor_metrics.sqlite")

def _ensure_db():
    conn = sqlite3.connect(_JANITOR_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS endpoint_calls (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          REAL    DEFAULT (unixepoch('now')),
            path        TEXT    NOT NULL,
            method      TEXT    NOT NULL,
            status_code INTEGER,
            elapsed_ms  REAL    NOT NULL,
            empresa_id  INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON endpoint_calls(path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ts   ON endpoint_calls(ts)")
    conn.commit()
    conn.close()

_ensure_db()

# ── Queue assíncrona para writes não-bloqueantes ──────────────────────────────
_write_queue: asyncio.Queue = None

async def _drain_writer():
    """Task daemon que drena a fila e persiste em batch no SQLite."""
    global _write_queue
    _write_queue = asyncio.Queue(maxsize=5000)
    conn = sqlite3.connect(_JANITOR_DB, check_same_thread=False)
    batch = []
    while True:
        try:
            item = await asyncio.wait_for(_write_queue.get(), timeout=2.0)
            batch.append(item)
            # Drena até 50 items por vez para micro-batch
            while not _write_queue.empty() and len(batch) < 50:
                batch.append(_write_queue.get_nowait())
        except asyncio.TimeoutError:
            pass

        if batch:
            try:
                conn.executemany(
                    "INSERT INTO endpoint_calls(path, method, status_code, elapsed_ms, empresa_id) VALUES (?,?,?,?,?)",
                    batch
                )
                conn.commit()
            except Exception:
                pass
            batch.clear()

async def start_profiler():
    """Chame no evento startup do FastAPI."""
    asyncio.create_task(_drain_writer())


# ── Middleware ─────────────────────────────────────────────────────────────────
class JanitorTimingMiddleware(BaseHTTPMiddleware):
    """
    Injeta X-Response-Time-Ms em cada resposta e persiste o timing.
    Rotas de assets estáticos são ignoradas.
    """
    SKIP_PREFIXES = ("/static", "/favicon", "/_", "/docs", "/openapi", "/redoc")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in self.SKIP_PREFIXES):
            return await call_next(request)

        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Header informativo
        response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.1f}"

        # Extrai empresa_id da query string se disponível
        empresa_id = None
        try:
            raw = request.query_params.get("empresa_id")
            empresa_id = int(raw) if raw else None
        except Exception:
            pass

        # Enfileira assincronamente (não bloqueia o request)
        if _write_queue and not _write_queue.full():
            try:
                _write_queue.put_nowait((
                    path,
                    request.method,
                    response.status_code,
                    round(elapsed_ms, 2),
                    empresa_id,
                ))
            except asyncio.QueueFull:
                pass

        return response


# ── API: gera relatório de performance ────────────────────────────────────────
def get_performance_report(top_n: int = 20, janela_horas: int = 24) -> dict:
    """
    Retorna estatísticas P50/P95/P99 por endpoint nas últimas N horas.
    Inclui endpoints mais lentos e endpoints mais chamados.
    """
    conn = sqlite3.connect(_JANITOR_DB)
    since_ts = time.time() - (janela_horas * 3600)

    rows = conn.execute("""
        SELECT path, method,
               COUNT(*)                                         AS n_calls,
               ROUND(AVG(elapsed_ms), 1)                       AS avg_ms,
               ROUND(MIN(elapsed_ms), 1)                       AS min_ms,
               ROUND(MAX(elapsed_ms), 1)                       AS max_ms,
               GROUP_CONCAT(elapsed_ms ORDER BY elapsed_ms)    AS sorted_ms_csv,
               COUNT(CASE WHEN status_code >= 500 THEN 1 END)  AS n_errors,
               MAX(ts)                                         AS last_seen_ts
        FROM endpoint_calls
        WHERE ts >= ?
        GROUP BY path, method
        ORDER BY avg_ms DESC
        LIMIT ?
    """, (since_ts, top_n)).fetchall()

    conn.close()

    endpoints = []
    for r in rows:
        vals = [float(x) for x in (r[6] or "0").split(",") if x]
        n = len(vals)
        p50 = vals[int(n * 0.50)] if n > 0 else 0
        p95 = vals[int(n * 0.95)] if n > 0 else 0
        p99 = vals[int(n * 0.99)] if n > 0 else 0
        endpoints.append({
            "path":        r[0],
            "method":      r[1],
            "n_calls":     r[2],
            "avg_ms":      r[3],
            "min_ms":      r[4],
            "max_ms":      r[5],
            "p50_ms":      round(p50, 1),
            "p95_ms":      round(p95, 1),
            "p99_ms":      round(p99, 1),
            "n_errors":    r[7],
            "last_seen":   r[8],
        })

    return {
        "janela_horas": janela_horas,
        "endpoints":    endpoints,
        "total_paths":  len(endpoints),
    }
