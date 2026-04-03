"""Main router for the Dashboard BI module.

Register in app/main.py:

    from app.modules.dashboard.router import router as dashboard_router
    app.include_router(dashboard_router, prefix="/api")
"""

from fastapi import APIRouter

from app.modules.dashboard.presentation.routes.dashboard_router import (
    router as dashboard_router,
)

router = APIRouter()
router.include_router(dashboard_router)
