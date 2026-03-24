"""Configuración global de tests.

Recrea el engine de SQLAlchemy entre tests de integración
para evitar contaminación de estado del connection pool.
"""

import pytest

from app.shared.database import session as db_session


@pytest.fixture(autouse=True)
async def _reset_db_engine():
    """Dispone el engine después de cada test para limpiar conexiones."""
    yield
    await db_session.engine.dispose()
