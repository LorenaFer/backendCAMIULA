from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Set, Tuple

from app.modules.auth.domain.entities.user import User


class UserRepository(ABC):

    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        ...

    @abstractmethod
    async def get_by_external_sub(
        self, provider: str, sub: str
    ) -> Optional[User]:
        """Find user by sub from an external provider (auth0, keycloak, etc.)."""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        ...

    @abstractmethod
    async def list_paginated(
        self, page: int, page_size: int
    ) -> Tuple[list[User], int]:
        ...

    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """Retorna el set de códigos de permisos activos del usuario.

        Complejidad: O(log n) — un solo query con JOINs indexados.
        """
        ...

    @abstractmethod
    async def get_user_roles(self, user_id: str) -> list[str]:
        """Retorna los nombres de roles activos del usuario."""
        ...
