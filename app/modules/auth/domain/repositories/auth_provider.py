"""
Interfaz abstracta del proveedor de autenticación.

Esta es LA ABSTRACCIÓN CLAVE de Clean Architecture para auth.
Implementar esta interfaz es el ÚNICO cambio necesario para migrar
de Auth0 a Keycloak, Firebase, o cualquier otro proveedor.

Implementaciones:
    - Auth0Provider  (producción)   → infrastructure/providers/auth0_provider.py
    - LocalAuthProvider (dev/test)  → infrastructure/providers/local_provider.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AuthProvider(ABC):

    @abstractmethod
    async def verify_token(self, token: str) -> dict:
        """Valida un JWT y retorna sus claims.

        Debe retornar al menos: {"sub": "...", "email": "..."}
        Lanza UnauthorizedException si el token es inválido.
        """
        ...

    @abstractmethod
    async def get_user_info(self, token: str) -> dict:
        """Obtiene información del usuario desde el proveedor."""
        ...
