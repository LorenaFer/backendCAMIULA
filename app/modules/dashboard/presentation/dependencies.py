"""Dependency injection factories for the Dashboard module (cross-cutting)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.infrastructure.dashboard_query_service import (
    DashboardQueryService,
)
from app.shared.database.session import get_db


def get_dashboard_service(
    session: AsyncSession = Depends(get_db),
) -> DashboardQueryService:
    return DashboardQueryService(session)
