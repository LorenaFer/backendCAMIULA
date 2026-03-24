"""Tests para Auth0Provider — valida la integración con el tenant real.

Estos tests verifican:
1. Que el JWKS endpoint del tenant es accesible
2. Que el provider rechaza tokens inválidos
3. Que la estructura del provider es correcta para Clean Architecture
"""

import pytest
import httpx

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException
from app.modules.auth.domain.repositories.auth_provider import AuthProvider
from app.modules.auth.infrastructure.providers.auth0_provider import Auth0Provider
from app.modules.auth.infrastructure.providers.local_provider import LocalAuthProvider

settings = get_settings()


class TestAuth0ProviderStructure:
    """Verifica que Auth0Provider implementa AuthProvider (Clean Architecture)."""

    def test_auth0_implements_interface(self):
        assert issubclass(Auth0Provider, AuthProvider)

    def test_local_implements_interface(self):
        assert issubclass(LocalAuthProvider, AuthProvider)

    def test_both_have_verify_token(self):
        assert hasattr(Auth0Provider, "verify_token")
        assert hasattr(LocalAuthProvider, "verify_token")

    def test_both_have_get_user_info(self):
        assert hasattr(Auth0Provider, "get_user_info")
        assert hasattr(LocalAuthProvider, "get_user_info")


class TestAuth0JWKS:
    """Verifica conectividad con el tenant Auth0 configurado."""

    @pytest.mark.skipif(
        not settings.AUTH0_DOMAIN,
        reason="AUTH0_DOMAIN not configured",
    )
    async def test_jwks_endpoint_accessible(self):
        """El JWKS endpoint del tenant debe ser accesible."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "keys" in data
        assert len(data["keys"]) > 0
        # Cada key debe tener kid y kty
        for key in data["keys"]:
            assert "kid" in key
            assert "kty" in key

    @pytest.mark.skipif(
        not settings.AUTH0_DOMAIN,
        reason="AUTH0_DOMAIN not configured",
    )
    async def test_openid_configuration_accessible(self):
        """El OpenID configuration endpoint debe ser accesible."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "issuer" in data
        assert settings.AUTH0_DOMAIN in data["issuer"]


class TestAuth0ProviderRejectsInvalidTokens:
    """Verifica que tokens inválidos son rechazados."""

    @pytest.mark.skipif(
        not settings.AUTH0_DOMAIN,
        reason="AUTH0_DOMAIN not configured",
    )
    async def test_rejects_garbage_token(self):
        provider = Auth0Provider(
            domain=settings.AUTH0_DOMAIN,
            audience=settings.AUTH0_API_AUDIENCE,
        )
        with pytest.raises(UnauthorizedException):
            await provider.verify_token("not.a.valid.token")

    @pytest.mark.skipif(
        not settings.AUTH0_DOMAIN,
        reason="AUTH0_DOMAIN not configured",
    )
    async def test_rejects_expired_token(self):
        """Un JWT con formato válido pero firmado con otra key debe fallar."""
        # Token HS256 firmado con secret local — Auth0 usa RS256
        from app.core.security import create_access_token

        local_token = create_access_token({"sub": "fake"})
        provider = Auth0Provider(
            domain=settings.AUTH0_DOMAIN,
            audience=settings.AUTH0_API_AUDIENCE,
        )
        with pytest.raises(UnauthorizedException):
            await provider.verify_token(local_token)


class TestLocalProvider:
    """Verifica que LocalAuthProvider funciona con tokens HS256 locales."""

    async def test_accepts_valid_local_token(self):
        from app.core.security import create_access_token

        token = create_access_token({"sub": "user-123", "email": "test@t.com"})
        provider = LocalAuthProvider()
        claims = await provider.verify_token(token)
        assert claims["sub"] == "user-123"
        assert claims["email"] == "test@t.com"

    async def test_rejects_invalid_token(self):
        provider = LocalAuthProvider()
        with pytest.raises(UnauthorizedException):
            await provider.verify_token("invalid.token.here")

    async def test_get_user_info(self):
        from app.core.security import create_access_token

        token = create_access_token({"sub": "u1", "email": "e@t.com"})
        provider = LocalAuthProvider()
        info = await provider.get_user_info(token)
        assert info["sub"] == "u1"
        assert info["email"] == "e@t.com"
