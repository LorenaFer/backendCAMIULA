"""
Script para testear la integración Auth0 end-to-end.

Pasos previos en Auth0 Dashboard (https://manage.auth0.com):

1. APIs → Create API:
   - Name: "CAMIULA API"
   - Identifier: lo que tengas en AUTH0_API_AUDIENCE (.env)
   - Signing Algorithm: RS256

2. Applications → Create Application:
   - Type: Machine to Machine
   - Name: "CAMIULA Test M2M"
   - Authorize para la API "CAMIULA API"
   - Copiar Client ID y Client Secret al .env

3. Ejecutar:
   python scripts/test_auth0.py

El script:
   ✓ Verifica conectividad con Auth0
   ✓ Obtiene un token M2M (client_credentials)
   ✓ Valida el token con Auth0Provider
   ✓ Prueba el endpoint /api/users/me con AUTH_PROVIDER=auth0
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx


async def main():
    from app.core.config import get_settings

    # Forzar recarga de settings
    get_settings.cache_clear()
    settings = get_settings()

    print("=" * 60)
    print("  TEST DE INTEGRACIÓN AUTH0")
    print("=" * 60)
    print()

    # --- Step 1: Verificar configuración ---
    print("[1/5] Verificando configuración...")
    issues = []
    if not settings.AUTH0_DOMAIN:
        issues.append("AUTH0_DOMAIN vacío en .env")
    if not settings.AUTH0_API_AUDIENCE:
        issues.append("AUTH0_API_AUDIENCE vacío en .env")
    if not settings.AUTH0_CLIENT_ID:
        issues.append("AUTH0_CLIENT_ID vacío en .env (necesario para test M2M)")
    if not settings.AUTH0_CLIENT_SECRET:
        issues.append("AUTH0_CLIENT_SECRET vacío en .env (necesario para test M2M)")

    if issues:
        print("  FALTAN VARIABLES EN .env:")
        for issue in issues:
            print(f"    - {issue}")
        print()
        print("  Configura estas variables y vuelve a ejecutar.")
        print("  Ver instrucciones al inicio de este archivo.")
        return

    print(f"  Domain:   {settings.AUTH0_DOMAIN}")
    print(f"  Audience: {settings.AUTH0_API_AUDIENCE}")
    print(f"  Client:   {settings.AUTH0_CLIENT_ID[:10]}...")
    print()

    async with httpx.AsyncClient(timeout=15.0) as client:

        # --- Step 2: Verificar JWKS ---
        print("[2/5] Verificando JWKS endpoint...")
        try:
            resp = await client.get(
                f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
            )
            resp.raise_for_status()
            keys = resp.json().get("keys", [])
            print(f"  OK — {len(keys)} keys encontradas")
            for key in keys:
                print(f"    kid={key['kid'][:20]}... alg={key.get('alg', 'N/A')}")
        except Exception as e:
            print(f"  ERROR — {e}")
            return
        print()

        # --- Step 3: Obtener token M2M ---
        print("[3/5] Obteniendo token M2M (client_credentials)...")
        try:
            resp = await client.post(
                f"https://{settings.AUTH0_DOMAIN}/oauth/token",
                json={
                    "client_id": settings.AUTH0_CLIENT_ID,
                    "client_secret": settings.AUTH0_CLIENT_SECRET,
                    "audience": settings.AUTH0_API_AUDIENCE,
                    "grant_type": "client_credentials",
                },
            )
            if resp.status_code != 200:
                print(f"  ERROR {resp.status_code}: {resp.text}")
                print()
                print("  Posibles causas:")
                print("  - Client ID o Secret incorrectos")
                print("  - La app M2M no está autorizada para la API")
                print("  - El Audience no coincide con el Identifier de la API")
                return

            token_data = resp.json()
            token = token_data["access_token"]
            print(f"  OK — Token obtenido ({len(token)} chars)")
            print(f"  Token type: {token_data.get('token_type')}")
            print(f"  Expires in: {token_data.get('expires_in')}s")
        except Exception as e:
            print(f"  ERROR — {e}")
            return
        print()

        # --- Step 4: Validar token con Auth0Provider ---
        print("[4/5] Validando token con Auth0Provider...")
        try:
            from app.modules.auth.infrastructure.providers.auth0_provider import (
                Auth0Provider,
            )

            provider = Auth0Provider(
                domain=settings.AUTH0_DOMAIN,
                audience=settings.AUTH0_API_AUDIENCE,
            )
            claims = await provider.verify_token(token)
            print(f"  OK — Token válido")
            print(f"  sub: {claims.get('sub', 'N/A')}")
            print(f"  iss: {claims.get('iss', 'N/A')}")
            print(f"  aud: {claims.get('aud', 'N/A')}")
        except Exception as e:
            print(f"  ERROR — {e}")
            return
        print()

        # --- Step 5: Probar contra el backend ---
        print("[5/5] Probando endpoint /api/users/me con token Auth0...")
        print("  (Nota: este test requiere que el servidor esté corriendo")
        print("   con AUTH_PROVIDER=auth0 y el usuario exista en la BD)")
        print()
        try:
            resp = await client.get(
                "http://localhost:8000/api/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            print(f"  Status: {resp.status_code}")
            print(f"  Response: {resp.json()}")

            if resp.status_code == 401:
                print()
                print("  Esto es esperado si el usuario Auth0 no existe en la BD.")
                print("  El token Auth0 ES VÁLIDO, pero no hay usuario local vinculado.")
                print("  Para vincular, necesitas crear un usuario con:")
                sub = claims.get("sub", "")
                print(f'    external_auth: {{"auth0": {{"sub": "{sub}"}}}}')
        except httpx.ConnectError:
            print("  Servidor no está corriendo en localhost:8000")
            print("  Ejecuta: AUTH_PROVIDER=auth0 uvicorn app.main:app --reload")
        except Exception as e:
            print(f"  ERROR — {e}")

    print()
    print("=" * 60)
    print("  TEST COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
