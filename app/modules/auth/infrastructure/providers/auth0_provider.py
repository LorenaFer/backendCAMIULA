"""
Proveedor Auth0 — para producción.

Valida JWTs RS256 usando JWKS (JSON Web Key Set) de Auth0.
Las claves JWKS se cachean en memoria con TTL para evitar
llamadas de red en cada request — O(1) en cache hit.
"""

from __future__ import annotations

import time
from typing import Optional

import httpx
from jose import jwt

from app.core.exceptions import UnauthorizedException
from app.modules.auth.domain.repositories.auth_provider import AuthProvider


class Auth0Provider(AuthProvider):

    def __init__(
        self,
        domain: str,
        audience: str,
        jwks_cache_ttl: int = 600,
    ) -> None:
        self._domain = domain
        self._audience = audience
        self._jwks_cache: Optional[dict] = None
        self._jwks_fetched_at: float = 0
        self._jwks_cache_ttl = jwks_cache_ttl
        self._http_client = httpx.AsyncClient(timeout=10.0)

    async def _get_signing_key(self, token: str) -> dict:
        """Obtiene la clave pública que firmó el token.

        O(1) en cache hit. O(1) amortizado en cache miss (1 fetch HTTP).
        """
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise UnauthorizedException("Token sin key ID")

        now = time.monotonic()
        if (
            self._jwks_cache is None
            or (now - self._jwks_fetched_at) > self._jwks_cache_ttl
        ):
            response = await self._http_client.get(
                f"https://{self._domain}/.well-known/jwks.json"
            )
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_fetched_at = now

        for key in self._jwks_cache.get("keys", []):
            if key["kid"] == kid:
                return key

        raise UnauthorizedException("No se encontró la clave de firma")

    async def verify_token(self, token: str) -> dict:
        try:
            jwk = await self._get_signing_key(token)
            payload = jwt.decode(
                token,
                jwk,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=f"https://{self._domain}/",
            )
            return payload
        except Exception as exc:
            raise UnauthorizedException(f"Token inválido: {exc}")

    async def get_user_info(self, token: str) -> dict:
        response = await self._http_client.get(
            f"https://{self._domain}/userinfo",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()
