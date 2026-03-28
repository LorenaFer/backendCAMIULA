from fastapi import APIRouter

from app.modules.form_schemas.presentation.routes.form_schema_routes import (
    router as form_schema_router,
)

router = APIRouter()
router.include_router(form_schema_router)
