from fastapi import APIRouter

from app.modules.appointments.presentation.routes.appointment_routes import (
    router as appointment_router,
)
from app.modules.appointments.presentation.routes.availability_routes import (
    router as availability_router,
)
from app.modules.appointments.presentation.routes.doctor_routes import (
    router as doctor_router,
)
from app.modules.appointments.presentation.routes.medical_record_routes import (
    router as medical_record_router,
)

router = APIRouter()
router.include_router(doctor_router)
router.include_router(availability_router)
router.include_router(appointment_router)
router.include_router(medical_record_router)
