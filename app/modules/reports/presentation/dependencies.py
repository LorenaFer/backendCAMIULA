"""Dependency injection factories for the Reports module (cross-cutting)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database.session import get_db


def get_db_session(
    session: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """Provide the DB session for EPI report query service functions."""
    return session
