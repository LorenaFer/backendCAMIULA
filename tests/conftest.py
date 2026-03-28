"""Configuración global de tests."""

import os

import pytest

# Forzar proveedor local para tests (independiente de lo que diga .env)
os.environ["AUTH_PROVIDER"] = "local"
os.environ["DEBUG"] = "False"


@pytest.fixture(autouse=True)
async def _reset_db_engine():
    """Dispone el engine después de cada test para limpiar conexiones."""
    # Limpiar el singleton del auth provider entre tests
    from app.shared.middleware import auth as auth_middleware

    auth_middleware._auth_provider = None

    yield

    from app.shared.database import session as db_session

    await db_session.engine.dispose()
