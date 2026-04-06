"""Main router for the Doctors module.

Aggregates all sub-routers under the /doctors prefix.
Register in app/main.py:

    from app.modules.doctors.router import router as doctors_router
    app.include_router(doctors_router, prefix="/api")
"""

from fastapi import APIRouter

from app.modules.doctors.presentation.routes.availability_router import (
    router as availability_router,
)
from app.modules.doctors.presentation.routes.doctors_router import (
    router as doctors_router,
)
from app.modules.doctors.presentation.routes.specialties_router import (
    router as specialties_router,
)

router = APIRouter()

router.include_router(specialties_router)
router.include_router(doctors_router)
router.include_router(availability_router)
