"""
Caché in-memory con TTL para permisos y roles de usuario.

Complejidad:
    - get/set/invalidate: O(1) — acceso a dict + comparación de timestamp.
    - Memoria: O(U × (P + R)) donde U = usuarios activos, P = permisos, R = roles.
      Con 1000 usuarios, 25 permisos y 2 roles cada uno: ~800 KB.

Para hardware de escasos recursos, esto es más eficiente que Redis
(evita proceso extra + network hop). Si se escala a múltiples workers,
migrar a Redis cambiando solo esta clase.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class UserAuthData:
    """Datos de autenticación cacheados para un usuario."""

    permissions: Set[str] = field(default_factory=set)
    roles: List[str] = field(default_factory=list)


class PermissionCache:

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._cache: Dict[str, Tuple[UserAuthData, float]] = {}
        self._ttl = ttl_seconds

    def _get_entry(self, user_id: str) -> Optional[UserAuthData]:
        """O(1) — dict lookup + timestamp check."""
        entry = self._cache.get(user_id)
        if entry is None:
            return None
        data, timestamp = entry
        if time.monotonic() - timestamp > self._ttl:
            del self._cache[user_id]
            return None
        return data

    # --- Permisos (retrocompatible) ---

    def get(self, user_id: str) -> Optional[Set[str]]:
        """O(1) — retorna permisos cacheados o None si no hay cache."""
        data = self._get_entry(user_id)
        return data.permissions if data else None

    def set(self, user_id: str, permissions: Set[str]) -> None:
        """O(1) — guarda permisos. Preserva roles si ya existían."""
        existing = self._get_entry(user_id)
        roles = existing.roles if existing else []
        self._cache[user_id] = (
            UserAuthData(permissions=permissions, roles=roles),
            time.monotonic(),
        )

    # --- Roles ---

    def get_roles(self, user_id: str) -> Optional[List[str]]:
        """O(1) — retorna roles cacheados o None si no hay cache."""
        data = self._get_entry(user_id)
        if data is None or not data.roles:
            return None
        return data.roles

    def set_roles(self, user_id: str, roles: List[str]) -> None:
        """O(1) — guarda roles. Preserva permisos si ya existían."""
        existing = self._get_entry(user_id)
        permissions = existing.permissions if existing else set()
        self._cache[user_id] = (
            UserAuthData(permissions=permissions, roles=roles),
            time.monotonic(),
        )

    # --- Combinado ---

    def set_all(self, user_id: str, permissions: Set[str], roles: List[str]) -> None:
        """O(1) — guarda permisos y roles juntos en un solo write."""
        self._cache[user_id] = (
            UserAuthData(permissions=permissions, roles=roles),
            time.monotonic(),
        )

    def invalidate(self, user_id: str) -> None:
        """O(1) — dict delete."""
        self._cache.pop(user_id, None)

    def clear(self) -> None:
        """O(1) — dict clear."""
        self._cache.clear()
