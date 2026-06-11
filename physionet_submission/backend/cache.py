"""
TriageAI — Lightweight Caching Layer
=====================================
Caches rarely-changing reference data (clinical-standards registry, model
metrics) so repeated requests do not hit disk / the database on every call.

Design:
  - In-process TTL cache by default (zero external dependencies, works in
    dev, tests, and single-instance deployments).
  - Optional Redis backend when REDIS_URL is set AND the `redis` package is
    installed — used transparently for multi-instance production deployments.

The public API is intentionally tiny: get(key), set(key, value, ttl),
get_or_set(key, producer, ttl), and clear(). Values must be JSON-serialisable
when a Redis backend is active.
"""
from __future__ import annotations

import json
import os
import threading
import time

DEFAULT_TTL = 300  # seconds


class _InMemoryTTLCache:
    """Thread-safe in-process cache with per-key expiry."""

    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at is not None and time.time() > expires_at:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key, value, ttl=DEFAULT_TTL):
        expires_at = (time.time() + ttl) if ttl else None
        with self._lock:
            self._store[key] = (expires_at, value)

    def clear(self):
        with self._lock:
            self._store.clear()


class _RedisCache:
    """Redis-backed cache. JSON-serialises values for portability."""

    def __init__(self, client):
        self._client = client

    def get(self, key):
        raw = self._client.get(key)
        return json.loads(raw) if raw is not None else None

    def set(self, key, value, ttl=DEFAULT_TTL):
        self._client.set(key, json.dumps(value), ex=ttl or None)

    def clear(self):
        self._client.flushdb()


def _build_backend():
    """Select Redis if configured & importable, else in-memory."""
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis  # type: ignore
            client = redis.Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            return _RedisCache(client)
        except Exception:
            # Any failure (package missing, server down) falls back gracefully.
            pass
    return _InMemoryTTLCache()


# Module-level singleton.
_backend = _build_backend()


def get(key):
    return _backend.get(key)


def set(key, value, ttl=DEFAULT_TTL):  # noqa: A001 - deliberate cache API name
    _backend.set(key, value, ttl)


def get_or_set(key, producer, ttl=DEFAULT_TTL):
    """Return cached value for `key`, or compute via `producer()`, cache, return."""
    cached = _backend.get(key)
    if cached is not None:
        return cached
    value = producer()
    _backend.set(key, value, ttl)
    return value


def clear():
    _backend.clear()


def backend_name():
    return "redis" if isinstance(_backend, _RedisCache) else "memory"
