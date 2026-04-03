"""Main router for the Medical Records module.

Registers sub-routers under /medical-records and /schemas.
Register in app/main.py:

    from app.modules.medical_records.router import router as medical_records_router
    app.include_router(medical_records_router, prefix="/api")
"""

from fastapi import APIRouter

from app.modules.medical_records.presentation.routes.medical_records_router import (
    router as records_router,
)
from app.modules.medical_records.presentation.routes.schemas_router import (
    router as schemas_router,
)

router = APIRouter()

router.include_router(records_router)
router.include_router(schemas_router)
