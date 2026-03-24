"""
Proveedor local de autenticación — para desarrollo y testing.

Reutiliza el sistema HS256 existente en app.core.security.
No requiere Auth0 ni conexión externa.
"""

from __future__ import annotations

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.modules.auth.domain.repositories.auth_provider import AuthProvider


class LocalAuthProvider(AuthProvider):

    async def verify_token(self, token: str) -> dict:
        payload = decode_access_token(token)
        if payload is None:
            raise UnauthorizedException("Token inválido o expirado")
        return payload

    async def get_user_info(self, token: str) -> dict:
        payload = await self.verify_token(token)
        return {"sub": payload.get("sub"), "email": payload.get("email")}
