from __future__ import annotations

from typing import Optional, Set

from app.core.exceptions import UnauthorizedException
from app.modules.auth.domain.entities.enums import UserStatus
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.repositories.auth_provider import AuthProvider
from app.modules.auth.domain.repositories.user_repository import UserRepository


class ValidateTokenUseCase:
    """Valida un JWT y retorna el usuario con permisos cargados.

    Se invoca en cada request autenticado.

    Complejidad:
        - Cache hit: O(1) — JWT decode + dict lookup.
        - Cache miss: O(log n) — 1 query JOIN indexado para cargar permisos.
    """

    def __init__(
        self,
        auth_provider: AuthProvider,
        user_repo: UserRepository,
        permission_cache: Optional[object] = None,
        auth_provider_name: str = "local",
    ) -> None:
        self._auth_provider = auth_provider
        self._user_repo = user_repo
        self._cache = permission_cache
        self._provider_name = auth_provider_name

    async def execute(self, token: str) -> User:
        claims = await self._auth_provider.verify_token(token)
        sub: str = claims.get("sub", "")

        if not sub:
            raise UnauthorizedException("Token sin identificador de usuario")

        # Buscar por ID (local) o por external_auth JSONB (Auth0, Keycloak, etc.)
        user = await self._user_repo.get_by_id(sub)
        if user is None and self._provider_name != "local":
            user = await self._user_repo.get_by_external_sub(
                self._provider_name, sub
            )

        if user is None:
            raise UnauthorizedException("Usuario no encontrado")

        if user.user_status == UserStatus.SUSPENDED.value:
            raise UnauthorizedException("Usuario suspendido")

        # Cargar permisos — O(1) cache hit, O(log n) cache miss
        cached: Optional[Set[str]] = None
        if self._cache is not None:
            cached = self._cache.get(user.id)

        if cached is not None:
            user.permissions = cached
        else:
            perms = await self._user_repo.get_user_permissions(user.id)
            user.permissions = perms
            if self._cache is not None:
                self._cache.set(user.id, perms)

        user.roles = await self._user_repo.get_user_roles(user.id)
        return user
