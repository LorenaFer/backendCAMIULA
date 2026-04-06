"""Router for the Reports module."""

from fastapi import APIRouter

from app.modules.reports.presentation.routes.epi_router import router as epi_router

router = APIRouter()
router.include_router(epi_router)
