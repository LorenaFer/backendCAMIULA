"""Router principal del modulo de Pacientes."""

from fastapi import APIRouter

from app.modules.patients.presentation.routes.patients_router import (
    router as patients_router,
)

router = APIRouter()
router.include_router(patients_router)
