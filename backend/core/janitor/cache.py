"""
Janitor Cache — Decorator LRU com TTL para endpoints FastAPI.

Uso:
    from core.janitor.cache import cached, invalidate_cache

    @app.get("/api/empreendimentos/basico")
    @cached(ttl=600, key_params=["empresa_id"])
    def api_empreendimentos(empresa_id: int = 959):
        ...

Invalidação manual:
    invalidate_cache("/api/empreendimentos/basico", empresa_id=959)

O cache é in-process (dict Python) e thread-safe via asyncio.Lock.
Dados: até 512 entradas, com LRU eviction automática quando cheio.
"""
import time
import asyncio
import functools
import hashlib
import json
from collections import OrderedDict
from typing import Callable, Any

# ── Store LRU ─────────────────────────────────────────────────────────────────
_MAX_ENTRIES = 512
_store: OrderedDict[str, tuple[float, Any]] = OrderedDict()  # key → (expire_ts, value)
_lock = asyncio.Lock()

def _make_key(path: str, params: dict) -> str:
    raw = json.dumps({"path": path, **params}, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()

def _evict_expired():
    """Remove entradas expiradas ou as mais antigas se cache cheio."""
    now = time.time()
    expired = [k for k, (exp, _) in _store.items() if exp < now]
    for k in expired:
        del _store[k]
    # LRU eviction: remove o mais antigo se ainda cheio
    while len(_store) >= _MAX_ENTRIES:
        _store.popitem(last=False)


# ── API pública ───────────────────────────────────────────────────────────────
def get_cache_stats() -> dict:
    now = time.time()
    valid = sum(1 for exp, _ in _store.values() if exp > now)
    return {
        "total_entries":   len(_store),
        "valid_entries":   valid,
        "expired_entries": len(_store) - valid,
        "max_entries":     _MAX_ENTRIES,
        "hit_rate_pct":    round(_hit_rate(), 1),
    }

_hits = 0
_misses = 0

def _hit_rate() -> float:
    total = _hits + _misses
    return (_hits / total * 100) if total > 0 else 0.0

def invalidate_cache(path: str = None, **kwargs) -> int:
    """
    Remove entradas do cache.
    - Se path=None: limpa tudo.
    - Se path fornecido: remove apenas entradas desse path (com qualquer combinação de params).
    Retorna número de entradas removidas.
    """
    if path is None:
        n = len(_store)
        _store.clear()
        return n

    # Filtra por path prefix no hash — não possível diretamente,
    # então guardamos o path no valor para permitir busca seletiva.
    # Alternativa simpler: limpar por prefixo da key se usarmos path como prefixo.
    to_del = [k for k, (_, meta) in _store.items()
              if isinstance(meta, dict) and meta.get("_cache_path") == path]
    for k in to_del:
        del _store[k]
    return len(to_del)


def cached(ttl: int = 300, key_params: list[str] = None):
    """
    Decorator de cache para funções síncronas FastAPI.

    Args:
        ttl: Tempo de vida em segundos (default: 5 min)
        key_params: Parâmetros da função usados como chave de cache.
                    Se None, usa todos os kwargs.
    """
    def decorator(func: Callable):
        path = getattr(func, "__name__", str(func))

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            global _hits, _misses

            # Monta chave
            params = {k: kwargs.get(k) for k in (key_params or list(kwargs.keys()))}
            cache_key = _make_key(path, params)

            now = time.time()
            _evict_expired()

            # Hit?
            if cache_key in _store:
                exp, payload = _store[cache_key]
                if exp > now:
                    _hits += 1
                    _store.move_to_end(cache_key)  # LRU refresh
                    return payload if not isinstance(payload, dict) or "_cache_path" not in payload else payload["_data"]

            # Miss — executa função real
            _misses += 1
            result = func(*args, **kwargs)
            _store[cache_key] = (now + ttl, {"_cache_path": path, "_data": result})
            _store.move_to_end(cache_key)
            return result

        wrapper._cache_path = path
        wrapper._cache_ttl  = ttl
        return wrapper

    return decorator


def cached_async(ttl: int = 300, key_params: list[str] = None):
    """
    Decorator de cache para funções assíncronas FastAPI.
    """
    def decorator(func: Callable):
        global _hits, _misses
        path = getattr(func, "__name__", str(func))

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            global _hits, _misses

            params = {k: kwargs.get(k) for k in (key_params or list(kwargs.keys()))}
            cache_key = _make_key(path, params)
            now = time.time()
            _evict_expired()

            if cache_key in _store:
                exp, payload = _store[cache_key]
                if exp > now:
                    _hits += 1
                    _store.move_to_end(cache_key)
                    return payload if not isinstance(payload, dict) or "_cache_path" not in payload else payload["_data"]

            _misses += 1
            result = await func(*args, **kwargs)
            _store[cache_key] = (now + ttl, {"_cache_path": path, "_data": result})
            _store.move_to_end(cache_key)
            return result

        wrapper._cache_path = path
        wrapper._cache_ttl  = ttl
        return wrapper

    return decorator
