"""
Middleware de autenticación y autorización.

Dependencies para FastAPI:
    - get_current_user_id()  — retorna solo el user_id (retrocompatible)
    - get_current_user()     — retorna User entity con roles y permisos
    - require_permission()   — verifica un permiso específico
    - require_any_permission() — verifica al menos uno de varios permisos
    - require_role()         — verifica un rol específico
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.repositories.auth_provider import AuthProvider
from app.modules.auth.domain.services.permission_service import PermissionService
from app.modules.auth.infrastructure.providers.auth0_provider import Auth0Provider
from app.modules.auth.infrastructure.providers.local_provider import LocalAuthProvider
from app.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.shared.database.session import get_db
from app.shared.middleware.permission_cache import permission_cache

settings = get_settings()
security_scheme = HTTPBearer()

# -- Auth Provider singleton --

_auth_provider: Optional[AuthProvider] = None


def get_auth_provider() -> AuthProvider:
    """Factory que retorna el proveedor configurado en AUTH_PROVIDER."""
    global _auth_provider
    if _auth_provider is None:
        if settings.AUTH_PROVIDER == "auth0":
            _auth_provider = Auth0Provider(
                domain=settings.AUTH0_DOMAIN,
                audience=settings.AUTH0_API_AUDIENCE,
            )
        else:
            _auth_provider = LocalAuthProvider()
    return _auth_provider


# -- Dependencies --


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> str:
    """Retorna solo el user_id del token. Retrocompatible."""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedException("Token inválido o expirado")
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Token sin identificador de usuario")
    return user_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Valida token, carga usuario con roles y permisos.

    Complejidad: O(1) cache hit, O(log n) cache miss.
    """
    provider = get_auth_provider()
    claims = await provider.verify_token(credentials.credentials)
    sub = claims.get("sub", "")

    if not sub:
        raise UnauthorizedException("Token sin identificador de usuario")

    repo = SQLAlchemyUserRepository(db)

    user = await repo.get_by_id(sub)
    if user is None and settings.AUTH_PROVIDER != "local":
        user = await repo.get_by_external_sub(settings.AUTH_PROVIDER, sub)

    if user is None:
        raise UnauthorizedException("Usuario no encontrado")

    if user.user_status == "SUSPENDED":
        raise UnauthorizedException("Usuario suspendido")

    # Permisos — O(1) cache hit
    cached_perms = permission_cache.get(user.id)
    if cached_perms is not None:
        user.permissions = cached_perms
    else:
        perms = await repo.get_user_permissions(user.id)
        permission_cache.set(user.id, perms)
        user.permissions = perms

    user.roles = await repo.get_user_roles(user.id)
    return user


def require_permission(permission: str):
    """Dependency factory: verifica que el usuario tenga un permiso.

    Uso: @router.get("/", dependencies=[Depends(require_permission("patients:read"))])
    O:   user: User = Depends(require_permission("patients:read"))
    """

    async def _check(user: User = Depends(get_current_user)) -> User:
        if not PermissionService.has_permission(user.permissions, permission):
            raise ForbiddenException(f"Permiso requerido: {permission}")
        return user

    return _check


def require_any_permission(*permissions: str):
    """Dependency factory: verifica al menos uno de los permisos."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        if not PermissionService.has_any_permission(
            user.permissions, set(permissions)
        ):
            raise ForbiddenException(
                f"Se requiere al menos uno de: {', '.join(permissions)}"
            )
        return user

    return _check


def require_role(role: str):
    """Dependency factory: verifica que el usuario tenga un rol."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        if role not in user.roles:
            raise ForbiddenException(f"Rol requerido: {role}")
        return user

    return _check
