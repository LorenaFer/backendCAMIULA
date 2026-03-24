"""
Lógica pura de dominio para verificación de permisos.
Sin dependencias de framework — solo Python puro y sets.
"""

from __future__ import annotations

from typing import Set


class PermissionService:

    @staticmethod
    def has_permission(user_permissions: Set[str], required: str) -> bool:
        """O(1) — membership check en hash set."""
        return required in user_permissions

    @staticmethod
    def has_any_permission(
        user_permissions: Set[str], required: Set[str]
    ) -> bool:
        """O(min(len(a), len(b))) — intersección de sets."""
        return bool(user_permissions & required)

    @staticmethod
    def has_all_permissions(
        user_permissions: Set[str], required: Set[str]
    ) -> bool:
        """O(len(required)) — subset check."""
        return required.issubset(user_permissions)

    @staticmethod
    def merge_role_permissions(role_permissions: list[Set[str]]) -> Set[str]:
        """O(total permisos) — unión de permisos de múltiples roles."""
        result: Set[str] = set()
        for perms in role_permissions:
            result |= perms
        return result
