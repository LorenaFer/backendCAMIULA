"""Router principal del modulo de Appointments."""

from fastapi import APIRouter

from app.modules.appointments.presentation.routes.appointments_router import (
    router as appointments_router,
)

router = APIRouter()
router.include_router(appointments_router)
