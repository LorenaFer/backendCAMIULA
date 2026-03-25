from fastapi import APIRouter

from app.modules.patients.presentation.routes.patient_routes import (
    router as patient_router,
)

router = APIRouter()
router.include_router(patient_router)
