"""
Caché in-memory con TTL para permisos de usuario.

Complejidad:
    - get/set/invalidate: O(1) — acceso a dict + comparación de timestamp.
    - Memoria: O(U × P) donde U = usuarios activos, P = permisos por usuario.
      Con 1000 usuarios y 25 permisos cada uno: ~750 KB.

Para hardware de escasos recursos, esto es más eficiente que Redis
(evita proceso extra + network hop). Si se escala a múltiples workers,
migrar a Redis cambiando solo esta clase.
"""

from __future__ import annotations

import time
from typing import Dict, Optional, Set, Tuple


class PermissionCache:

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._cache: Dict[str, Tuple[Set[str], float]] = {}
        self._ttl = ttl_seconds

    def get(self, user_id: str) -> Optional[Set[str]]:
        """O(1) — dict lookup + timestamp check."""
        entry = self._cache.get(user_id)
        if entry is None:
            return None
        permissions, timestamp = entry
        if time.monotonic() - timestamp > self._ttl:
            del self._cache[user_id]
            return None
        return permissions

    def set(self, user_id: str, permissions: Set[str]) -> None:
        """O(1) — dict assignment."""
        self._cache[user_id] = (permissions, time.monotonic())

    def invalidate(self, user_id: str) -> None:
        """O(1) — dict delete."""
        self._cache.pop(user_id, None)

    def clear(self) -> None:
        """O(1) — dict clear."""
        self._cache.clear()
