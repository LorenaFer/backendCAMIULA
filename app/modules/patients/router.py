from fastapi import APIRouter

from app.modules.patients.presentation.routes.patients_routes import (
    router as patients_router,
)

router = APIRouter()
router.include_router(patients_router)
